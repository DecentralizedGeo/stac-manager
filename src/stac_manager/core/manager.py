"""Workflow orchestration and execution management."""
import logging
from pathlib import Path
from typing import Any
from dataclasses import dataclass
from typing import Literal
from stac_manager.exceptions import ConfigurationError
from stac_manager.core.config import WorkflowDefinition, build_execution_order
from stac_manager.core.context import WorkflowContext
from stac_manager.core.failures import FailureCollector
from stac_manager.core.checkpoints import CheckpointManager
from stac_manager.protocols import Fetcher, Modifier, Bundler


# Module registry: Maps module names to their import paths
MODULE_REGISTRY: dict[str, str] = {
    'IngestModule': 'stac_manager.modules.ingest',
    'SeedModule': 'stac_manager.modules.seed',
    'TransformModule': 'stac_manager.modules.transform',
    'UpdateModule': 'stac_manager.modules.update',
    'ExtensionModule': 'stac_manager.modules.extension',
    'ValidateModule': 'stac_manager.modules.validate',
    'OutputModule': 'stac_manager.modules.output',
}


def load_module_class(module_name: str) -> type:
    """
    Dynamically import and return module class.
    
    Args:
        module_name: Class name from workflow YAML (e.g., 'IngestModule')
        
    Returns:
        Module class (not instance)
        
    Raises:
        ConfigurationError: If module not found in registry or import fails
    """
    if module_name not in MODULE_REGISTRY:
        raise ConfigurationError(f"Unknown module: {module_name}")
    
    module_path = MODULE_REGISTRY[module_name]
    
    try:
        # Import module
        import importlib
        module = importlib.import_module(module_path)
        
        # Get class from module
        return getattr(module, module_name)
    except (ImportError, AttributeError) as e:
        raise ConfigurationError(f"Failed to load module {module_name}: {e}") from e


@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    success: bool
    status: Literal['completed', 'completed_with_failures', 'failed']
    summary: str
    failure_count: int
    total_items_processed: int


class StacManager:
    """
    Main orchestrator for executing STAC Manager pipelines.
    
    Responsibilities:
    - Load and validate configuration
    - Build execution order (DAG resolution)
    - Instantiate modules
    - Execute pipeline (sequential streaming)
    - Handle matrix strategy (parallel pipelines)
    """
    
    def __init__(
        self,
        config: dict | WorkflowDefinition,
        checkpoint_dir: Path | None = None,
        log_level: str = "INFO"
    ):
        """
        Initialize StacManager with workflow configuration.
        
        Args:
            config: Workflow configuration (dict or WorkflowDefinition)
            checkpoint_dir: Directory for checkpoint storage (default: ./checkpoints)
            log_level: Logging level (default: INFO)
            
        Raises:
            ConfigurationError: If configuration invalid or DAG has cycles
        """
        # Convert dict to WorkflowDefinition if needed
        if isinstance(config, dict):
            self.workflow = WorkflowDefinition(**config)
        else:
            self.workflow = config
        
        # Setup checkpoint directory
        self.checkpoint_dir = checkpoint_dir or Path('./checkpoints')
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger(f"stac_manager.{self.workflow.name}")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Build execution order (validates DAG, detects cycles)
        self._execution_order = build_execution_order(self.workflow.steps)
        
        self.logger.info(
            f"Initialized workflow '{self.workflow.name}' "
            f"with {len(self.workflow.steps)} steps"
        )
        self.logger.debug(f"Execution order: {self._execution_order}")
    
    def _instantiate_modules(self, context: WorkflowContext) -> dict[str, Any]:
        """
        Instantiate all modules for the workflow.
        
        Args:
            context: Workflow execution context
            
        Returns:
            Dictionary mapping step_id to instantiated module
            
        Raises:
            ConfigurationError: If module instantiation fails
        """
        modules = {}
        
        for step in self.workflow.steps:
            try:
                # Load module class
                module_class = load_module_class(step.module)
                
                # Instantiate with config
                module_instance = module_class(config=step.config)
                
                modules[step.id] = module_instance
                
                self.logger.debug(
                    f"Instantiated {step.module} for step '{step.id}'"
                )
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to instantiate module for step '{step.id}': {e}"
                ) from e
        
        return modules
    
    async def execute(self) -> WorkflowResult:
        """
        Execute the configured workflow pipeline.
        
        Returns:
            WorkflowResult with execution summary
            
        Raises:
            ConfigurationError: If critical error during execution
        """
        self.logger.info(f"Starting workflow '{self.workflow.name}'")
        
        # Initialize workflow context
        failure_collector = FailureCollector()
        checkpoint_manager = CheckpointManager(
            workflow_id=self.workflow.name,
            collection_id="default",
            checkpoint_root=self.checkpoint_dir,
            resume_from_existing=self.workflow.resume_from_checkpoint
        )
        
        context = WorkflowContext(
            workflow_id=self.workflow.name,
            config={},
            logger=self.logger,
            failure_collector=failure_collector,
            checkpoints=checkpoint_manager,
            data={}
        )
        
        # Instantiate modules
        modules = self._instantiate_modules(context)
        
        # Execute pipeline steps in order
        total_items = await self._execute_pipeline(modules, context)
        
        # Generate result
        failures = failure_collector.get_all()
        failure_count = len(failures)
        
        if failure_count == 0:
            status = 'completed'
            success = True
        elif failure_count < total_items:
            status = 'completed_with_failures'
            success = True
        else:
            status = 'failed'
            success = False
        
        self.logger.info(
            f"Workflow '{self.workflow.name}' {status}: "
            f"{total_items} items processed, {failure_count} failures"
        )
        
        return WorkflowResult(
            success=success,
            status=status,
            summary=f"Processed {total_items} items with {failure_count} failures",
            failure_count=failure_count,
            total_items_processed=total_items
        )
    
    async def _execute_pipeline(
        self,
        modules: dict[str, Any],
        context: WorkflowContext
    ) -> int:
        """
        Execute pipeline steps in sequential order with streaming.
        
        Args:
            modules: Instantiated modules keyed by step_id
            context: Workflow execution context
            
        Returns:
            Total number of items processed
        """
        stream = None
        total_items = 0
        
        for step_id in self._execution_order:
            module = modules[step_id]
            step_config = next(s for s in self.workflow.steps if s.id == step_id)
            
            self.logger.info(f"Executing step '{step_id}' ({step_config.module})")
            
            # Execute based on protocol
            if isinstance(module, Fetcher):
                # Start new stream from fetcher
                stream = module.fetch(context)
                
            elif isinstance(module, Modifier):
                # Wrap modifier in async generator
                if stream is None:
                    raise ConfigurationError(
                        f"Modifier step '{step_id}' has no input stream"
                    )
                stream = self._wrap_modifier(module, stream, context, step_id)
                
            elif isinstance(module, Bundler):
                # Drain stream to bundler (final step)
                if stream is None:
                    raise ConfigurationError(
                        f"Bundler step '{step_id}' has no input stream"
                    )
                total_items = await self._drain_to_bundler(
                    module, stream, context, step_id
                )
                
                # Finalize bundler
                await module.finalize(context)
        
        return total_items
    
    async def _wrap_modifier(
        self,
        modifier: Modifier,
        stream: Any,
        context: WorkflowContext,
        step_id: str
    ):
        """Wrap sync modifier in async generator."""
        async for item in stream:
            try:
                result = modifier.modify(item, context)
                if result:
                    yield result
            except Exception as e:
                self.logger.warning(
                    f"Modifier '{step_id}' failed for item {item.get('id', 'unknown')}: {e}"
                )
                context.failure_collector.add(
                    item_id=item.get('id', 'unknown'),
                    error=e,
                    step_id=step_id
                )
    
    async def _drain_to_bundler(
        self,
        bundler: Bundler,
        stream: Any,
        context: WorkflowContext,
        step_id: str
    ) -> int:
        """Drain stream to bundler and count items."""
        count = 0
        
        async for item in stream:
            try:
                await bundler.bundle(item, context)
                count += 1
                
                if count % 100 == 0:
                    self.logger.debug(f"Processed {count} items through '{step_id}'")
                    
            except Exception as e:
                self.logger.warning(
                    f"Bundler '{step_id}' failed for item {item.get('id', 'unknown')}: {e}"
                )
                context.failure_collector.add(
                    item_id=item.get('id', 'unknown'),
                    error=e,
                    step_id=step_id
                )
        
        self.logger.info(f"Step '{step_id}' processed {count} items")
        return count
