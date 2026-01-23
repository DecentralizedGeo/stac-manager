"""Extension Module - STAC extension scaffolding."""
import requests
from stac_manager.modules.config import ExtensionConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import ConfigurationError
from stac_manager.utils.field_ops import deep_merge


class ExtensionModule:
    """Applies STAC extensions via schema scaffolding."""
    
    def __init__(self, config: dict) -> None:
        """Initialize and fetch schema."""
        self.config = ExtensionConfig(**config)
        
        # Fetch schema
        try:
            response = requests.get(self.config.schema_uri, timeout=10)
            response.raise_for_status()
            self.schema = response.json()
        except requests.RequestException as e:
            raise ConfigurationError(f"Failed to fetch schema from {self.config.schema_uri}: {e}")
        
        # Build template
        self.template = self._build_template(self.schema)
        
        # Apply user defaults over template
        if self.config.defaults:
            self.template = deep_merge(self.template, self.config.defaults, strategy='overwrite')
    
    def _build_template(self, schema: dict) -> dict:
        """
        Parse JSON Schema to build scaffolding template.
        
        Args:
            schema: JSON Schema dict
        
        Returns:
            Template dict with null values
        """
        template = {"properties": {}}
        
        target_props = {}
        
        # Handle direct properties
        if "properties" in schema:
            schema_props = schema["properties"]
            if "properties" in schema_props and "properties" in schema_props["properties"]:
                # Nested structure: schema.properties.properties.properties
                target_props = schema_props["properties"]["properties"]
        
        # Handle oneOf variants
        elif "oneOf" in schema:
            for variant in schema["oneOf"]:
                if variant.get("properties", {}).get("type", {}).get("const") == "Feature":
                    # Found STAC Item definition
                    if "properties" in variant.get("properties", {}):
                        props_def = variant["properties"]["properties"]
                        if "properties" in props_def:
                            target_props = props_def["properties"]
                    break
        
        # Build template from extracted properties
        for key, field_def in target_props.items():
            default_val = field_def.get("default", None)
            template["properties"][key] = default_val
        
        return template
    
    def modify(self, item: dict, context: WorkflowContext) -> dict:
        """
        Apply extension to item.
        
        Args:
            item: STAC item dict
            context: Workflow context
        
        Returns:
            Item with extension applied
        """
        # 1. Tag extension
        if "stac_extensions" not in item:
            item["stac_extensions"] = []
        
        if self.config.schema_uri not in item["stac_extensions"]:
            item["stac_extensions"].append(self.config.schema_uri)
        
        # 2. Merge template (keep existing values)
        item = deep_merge(item, self.template, strategy='keep_existing')
        
        return item
