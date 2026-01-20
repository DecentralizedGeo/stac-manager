from typing import Dict, Any, Protocol, Optional
from pydantic import BaseModel, Field
import pystac
from stac_manager.context import WorkflowContext

class Extension(Protocol):
    """Protocol that custom extensions must implement."""
    extension_name: str
    schema_url: str
    def apply(self, item: pystac.Item, config: dict) -> pystac.Item: ...

class ExtensionConfig(BaseModel):
    extension: str
    config: Dict[str, Any] = Field(default_factory=dict)
    should_validate: bool = Field(default=False, alias="validate")
    schema_uri: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None

class ExtensionModule:
    """Applies a custom extension to an item."""
    
    def __init__(self, config: dict):
        self.config = ExtensionConfig(**config)
        # TODO: Implement dynamic loading via importlib or registry
        # For v1.0, we just assume a placeholder or raise NotImplemented for unknown extensions
        # if not defined.
    
    def modify(self, item: dict, context: WorkflowContext) -> dict | None:
        context.logger.debug(f"Applying extension {self.config.extension}")
        
        # Special handling for Generic Extension
        if self.config.extension == "generic":
            return self._apply_generic(item)

        # 1. Convert to PySTAC
        try:
            stac_item = pystac.Item.from_dict(item)
        except Exception as e:
            # If conversion fails, drop or log failure. 
            # For robustness, we assume valid dicts from upstream or return None
            context.logger.error(f"Extension module failed to parse item: {e}", exc_info=True)
            return None
            
        # 2. Apply Logic (Placeholder for real dynamic loading)
        # ext = self._load_extension(self.config.extension)
        # stac_item = ext.apply(stac_item, self.config.config)
        
        # 3. Return dict
        return stac_item.to_dict()

    def _apply_generic(self, item: dict) -> dict:
        if self.config.schema_uri:
            schemas = item.setdefault("stac_extensions", [])
            if self.config.schema_uri not in schemas:
                schemas.append(self.config.schema_uri)

        if self.config.properties:
            props = item.setdefault("properties", {})
            props.update(self.config.properties)
            
        return item
    
    def _load_extension(self, name: str) -> Extension:
        # Placeholder for dynamic loading
        raise NotImplementedError("Dynamic extension loading not yet implemented for v1.0")
