"""Workflow orchestration and execution management."""
from stac_manager.exceptions import ConfigurationError


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
