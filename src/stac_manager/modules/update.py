from typing import Dict, Any, Literal
from pydantic import BaseModel
from stac_manager.context import WorkflowContext

class UpdateConfig(BaseModel):
    updates: Dict[str, Any]
    mode: Literal['merge', 'replace'] = 'merge'

class UpdateModule:
    """Updates metadata fields based on configuration paths."""
    
    def __init__(self, config: dict):
        self.config = UpdateConfig(**config)
        
    def modify(self, item: dict, context: WorkflowContext) -> dict:
        context.logger.debug(f"Updating item {item.get('id')} with {len(self.config.updates)} changes")
        for path, value in self.config.updates.items():
            context.logger.debug(f"Applying update {path} -> {value}")
            self._apply_update(item, path.split('.'), value)
        return item
        
    def _apply_update(self, obj: Any, keys: list[str], value: Any):
        key = keys[0]
        if len(keys) == 1:
            obj[key] = value
        else:
            if key not in obj:
                obj[key] = {} # Create missing dict if merging
            elif not isinstance(obj[key], dict):
                # If we hit a non-dict where we need to traverse, and mode is merge... 
                # actually pure JSON traversal would expect dicts. 
                # If it's a list, we can't key into it with string.
                # Simplification: assume dict structure for nested updates.
                pass
            
            self._apply_update(obj[key], keys[1:], value)
