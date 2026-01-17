from importlib import import_module
from stac_manager.exceptions import WorkflowConfigError
from typing import Type, Any

MODULE_REGISTRY = {
    'DiscoveryModule': 'stac_manager.modules.discovery.DiscoveryModule',
    'IngestModule': 'stac_manager.modules.ingest.IngestModule',
    'TransformModule': 'stac_manager.modules.transform.TransformModule',
    'ScaffoldModule': 'stac_manager.modules.scaffold.ScaffoldModule',
    'ExtensionModule': 'stac_manager.modules.extension.ExtensionModule',
    'ValidateModule': 'stac_manager.modules.validate.ValidateModule',
    'UpdateModule': 'stac_manager.modules.update.UpdateModule',
    'OutputModule': 'stac_manager.modules.output.OutputModule',
}

def get_module_class(module_name: str) -> Type[Any]:
    if module_name not in MODULE_REGISTRY:
        raise WorkflowConfigError(f"Unknown module: {module_name}")
    
    module_path = MODULE_REGISTRY[module_name]
    try:
        mod_name, cls_name = module_path.rsplit('.', 1)
        # Note: We are importing the module, but not yet verifying the class exists/is valid
        # because the modules don't exist yet!
        # In a real scenario, we might want to catch ImportError and check if it's the target module.
        # For this test (get_unknown_module), we just need to fail the lookup.
        
        # To make the test pass without creating all modules yet, we defer the import 
        # or just handle the error. But the Requirement says "Implement Registry" as Step 3.
        # The test expects WorkflowConfigError for "UnknownModule".
        # If we pass a known module that doesn't exist, import_module raises ModuleNotFoundError.
        
        mod = import_module(mod_name)
        return getattr(mod, cls_name)
    except (ImportError, AttributeError) as e:
        # Wrap import errors into config errors if it was a registry issue?
        # But if the module is in registry but not found on disk, it's also effectively a config/env error.
        raise WorkflowConfigError(f"Failed to load module {module_name} from {module_path}: {e}")
