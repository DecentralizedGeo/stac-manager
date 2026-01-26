"""Workflow orchestration and execution management."""
import logging
from pathlib import Path
from typing import Any
from stac_manager.exceptions import ConfigurationError
from stac_manager.core.config import WorkflowDefinition, build_execution_order
from stac_manager.core.context import WorkflowContext


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
