"""Workflow orchestration and execution management."""
import logging
import asyncio
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
    matrix_entry: dict[str, Any] | None = None  # Track which matrix entry this result is for
    failure_collector: FailureCollector | None = None  # Access to failure details


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
        
        # Setup logging - prefer workflow config over CLI parameter
        self.logger = logging.getLogger(f"stac_manager.{self.workflow.name}")
        
        # Use log level from workflow settings if available, otherwise use parameter
        if self.workflow.settings and 'logging' in self.workflow.settings:
            workflow_log_level = self.workflow.settings['logging'].get('level', log_level)
        else:
            workflow_log_level = log_level
            
        self.logger.setLevel(getattr(logging, workflow_log_level.upper()))
        
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
        
        Matrix context data from context.data is merged into step configs,
        allowing matrix entries to override or extend step configuration.
        
        Creates step-specific loggers for each module and injects them if the
        module supports the set_logger() method.
        
        Args:
            context: Workflow execution context (contains matrix data in context.data)
            
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
                
                # Merge matrix context data into step config
                # Matrix data from context.data takes precedence for matching keys
                merged_config = {**step.config, **context.data}
                
                # Instantiate with merged config
                module_instance = module_class(config=merged_config)
                
                # Create and inject step-specific logger
                step_logger = logging.getLogger(f"{self.logger.name}.{step.id}")
                
                # Set step-specific log level if configured, otherwise inherit from parent
                if step.log_level:
                    try:
                        level = getattr(logging, step.log_level.upper())
                        step_logger.setLevel(level)
                        self.logger.debug(
                            f"Set log level for step '{step.id}' to {step.log_level.upper()}"
                        )
                    except AttributeError:
                        self.logger.warning(
                            f"Invalid log level '{step.log_level}' for step '{step.id}', using default"
                        )
                else:
                    # Inherit the global logger's level
                    step_logger.setLevel(self.logger.level)
                    self.logger.info(
                        f"Step '{step.id}' logger level set to {logging.getLevelName(self.logger.level)} (inherited from global)"
                    )
                
                # Inject logger into module if it supports it
                if hasattr(module_instance, 'set_logger'):
                    module_instance.set_logger(step_logger)
                    self.logger.debug(
                        f"Injected logger for step '{step.id}' into {step.module}"
                    )
                
                modules[step.id] = module_instance
                
                self.logger.debug(
                    f"Instantiated {step.module} for step '{step.id}'"
                )
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to instantiate module for step '{step.id}': {e}"
                ) from e
        
        return modules
    
    async def execute(self) -> WorkflowResult | list[WorkflowResult]:
        """
        Execute the configured workflow pipeline.
        
        Supports both single pipeline and matrix strategy (parallel pipelines).
        
        Returns:
            WorkflowResult for single pipeline, or list of WorkflowResult for matrix strategy
            
        Raises:
            ConfigurationError: If critical error during execution
        """
        # Check for matrix strategy
        if self.workflow.strategy.matrix:
            return await self._execute_matrix()
        else:
            return await self._execute_single()
    
    async def _execute_single(self, matrix_entry: dict[str, Any] | None = None) -> WorkflowResult:
        """
        Execute a single pipeline instance.
        
        Args:
            matrix_entry: Optional matrix entry data to merge into step configs
            
        Returns:
            WorkflowResult with execution summary
        """
        workflow_id = self.workflow.name
        if matrix_entry and "collection_id" in matrix_entry:
            workflow_id = f"{self.workflow.name}-{matrix_entry['collection_id']}"
        
        self.logger.info(f"Starting workflow '{workflow_id}'")
        
        # Initialize workflow context
        failure_collector = FailureCollector()
        checkpoint_manager = CheckpointManager(
            workflow_id=workflow_id,
            collection_id=matrix_entry.get("collection_id", "default") if matrix_entry else "default",
            checkpoint_root=self.checkpoint_dir,
            resume_from_existing=self.workflow.resume_from_checkpoint
        )
        
        context = WorkflowContext(
            workflow_id=workflow_id,
            config={},
            logger=self.logger,
            failure_collector=failure_collector,
            checkpoints=checkpoint_manager,
            data=matrix_entry or {}  # Inject matrix data into context for config merging
        )
        
        try:
            # Instantiate modules (will merge matrix data into configs)
            modules = self._instantiate_modules(context)
            
            # Execute pipeline steps in order
            total_items = await self._execute_pipeline(modules, context)
        except Exception as e:
            # Critical failure during execution
            self.logger.error(f"Critical error in workflow '{workflow_id}': {e}")
            return WorkflowResult(
                success=False,
                status='failed',
                summary=f"Critical error: {e}",
                failure_count=0,
                total_items_processed=0,
                matrix_entry=matrix_entry,
                failure_collector=failure_collector
            )
        
        # Generate result
        failures = failure_collector.get_all()
        failure_count = len(failures)
        
        # Determine status based on failures
        if total_items == 0:
            status = 'failed'
            success = False
        elif failure_count == 0:
            status = 'completed'
            success = True
        elif failure_count < total_items:
            status = 'completed_with_failures'
            success = True
        else:
            status = 'failed'
            success = False
        
        self.logger.info(
            f"Workflow '{workflow_id}' {status}: "
            f"{total_items} items processed, {failure_count} failures"
        )
        
        return WorkflowResult(
            success=success,
            status=status,
            summary=f"Processed {total_items} items with {failure_count} failures",
            failure_count=failure_count,
            total_items_processed=total_items,
            matrix_entry=matrix_entry,
            failure_collector=failure_collector  # Include failure collector for inspection
        )
    
    async def _execute_matrix(self) -> list[WorkflowResult]:
        """
        Execute multiple parallel pipelines for matrix strategy.
        
        Each matrix entry spawns an independent pipeline execution.
        Failures in one pipeline don't affect others.
        
        Returns:
            List of WorkflowResult (one per matrix entry)
        """
        matrix = self.workflow.strategy.matrix
        self.logger.info(
            f"Executing matrix strategy with {len(matrix)} parallel pipelines"
        )
        
        # Execute all matrix entries in parallel
        tasks = [
            self._execute_single(matrix_entry=entry)
            for entry in matrix
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to failed results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(
                    f"Matrix entry {i} failed with exception: {result}"
                )
                final_results.append(
                    WorkflowResult(
                        success=False,
                        status='failed',
                        summary=f"Exception: {result}",
                        failure_count=0,
                        total_items_processed=0,
                        matrix_entry=matrix[i]
                    )
                )
            else:
                final_results.append(result)
        
        # Log summary
        successful = sum(1 for r in final_results if r.success)
        self.logger.info(
            f"Matrix strategy completed: {successful}/{len(matrix)} pipelines succeeded"
        )
        
        return final_results
    
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
            if item is None:
                continue
            try:
                result = modifier.modify(item, context)
                if result:
                    yield result
            except Exception as e:
                self.logger.warning(
                    f"Modifier '{step_id}' failed for item {item.get('id', 'unknown') if item else 'unknown'}: {e}"
                )
                context.failure_collector.add(
                    item_id=item.get('id', 'unknown') if item else 'unknown',
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
            if item is None:
                continue
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
