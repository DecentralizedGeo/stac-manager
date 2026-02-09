"""Extension Module - STAC extension scaffolding."""
import logging
import requests
import pystac
from pystac import EXTENSION_HOOKS
from typing import Any
from stac_manager.modules.config import ExtensionConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import ConfigurationError
from stac_manager.utils.field_ops import deep_merge, set_nested_field, expand_wildcard_paths, dot_notation_to_nested


class ExtensionModule:
    """Applies STAC extensions via schema scaffolding."""
    
    def __init__(self, config: dict) -> None:
        """Initialize and fetch schema."""
        self.config = ExtensionConfig(**config)
        self.logger = logging.getLogger(__name__)  # Default logger
        self.is_registered = False
        
        # Check if extension is registered with pystac
        try:
            # Check if schema_uri is directly registered
            if self.config.schema_uri in EXTENSION_HOOKS.hooks:
                self.is_registered = True
            else:
                # Check if schema_uri matches any previous extension IDs
                for hook in EXTENSION_HOOKS.hooks.values():
                    if self.config.schema_uri in hook.prev_extension_ids:
                        self.is_registered = True
                        break
        except Exception:
            pass
        
        # Fetch schema
        try:
            response = requests.get(self.config.schema_uri, timeout=10)
            response.raise_for_status()
            self.schema = response.json()
        except requests.RequestException as e:
            raise ConfigurationError(f"Failed to fetch schema from {self.config.schema_uri}: {e}")
        
        # Build template
        self.template = self._build_template(self.schema)
        
        # Store raw defaults (will be expanded per-item to support wildcards)
        self.raw_defaults = self.config.defaults or {}
            
        # Apply non-wildcard defaults to template
        if self.raw_defaults:
            non_wildcard_defaults = {k: v for k, v in self.raw_defaults.items() if "*" not in k}
            if non_wildcard_defaults:
                if any("." in key for key in non_wildcard_defaults.keys()):
                    nested_defaults = dot_notation_to_nested(non_wildcard_defaults)
                else:
                    nested_defaults = non_wildcard_defaults
                self.template = deep_merge(self.template, nested_defaults, strategy='overwrite')
    
    def set_logger(self, logger: logging.Logger) -> None:
        """Set step-specific logger for this module.
        
        Args:
            logger: Logger instance to use for this module
        """
        self.logger = logger
    
    def _resolve_ref(self, ref: str, schema: dict) -> dict:
        """
        Resolve a local JSON Schema reference.
        
        Args:
            ref: Reference string (e.g., #/definitions/foo)
            schema: Root schema to resolve from
        
        Returns:
            Resolved definition dict
        """
        if not ref.startswith("#/"):
            return {}
        
        parts = ref.split("/")[1:]
        current = schema
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return {}
        return current

    def _parse_field(self, definition: dict, schema: dict) -> Any:
        """
        Parse a field definition to return its scaffolded value.
        
        Args:
            definition: Field definition dict
            schema: Root schema for ref resolution
            
        Returns:
            Value (dict for objects, default/None for others)
        """
        if "$ref" in definition:
            resolved = self._resolve_ref(definition["$ref"], schema)
            return self._parse_field(resolved, schema)
        
        if "allOf" in definition:
            template = {}
            for item in definition["allOf"]:
                val = self._parse_field(item, schema)
                if isinstance(val, dict):
                    template.update(val)
            return template

        # If it's an object, parse its properties
        properties = definition.get("properties", {})
        if properties or definition.get("type") == "object":
            template = {}
            required = definition.get("required", [])
            for key, prop_def in properties.items():
                if self.config.required_fields_only and key not in required:
                    continue
                template[key] = self._parse_field(prop_def, schema)
            return template
        
        # Leaf node: return default or None
        return definition.get("default", None)

    def _build_template(self, schema: dict) -> dict:
        """
        Parse JSON Schema to build scaffolding template.
        
        Args:
            schema: JSON Schema dict
        
        Returns:
            Template dict with null values
        """
        template = {"properties": {}, "assets": {}}
        
        # Handle direct properties (legacy support)
        if "properties" in schema and "properties" in schema["properties"]:
             # Nested structure: schema.properties.properties
             props_def = schema["properties"]["properties"]
             template["properties"] = self._parse_field(props_def, schema)
        
        # Handle oneOf variants (Standard STAC Extension pattern)
        if "oneOf" in schema:
            for variant in schema["oneOf"]:
                # Look for the Item/Feature variant
                if variant.get("properties", {}).get("type", {}).get("const") == "Feature":
                    variant_props = variant.get("properties", {})
                    
                    # 1. Properties extension
                    if "properties" in variant_props:
                        # Properties definition is an object
                        val = self._parse_field(variant_props["properties"], schema)
                        if isinstance(val, dict):
                            template["properties"].update(val)
                    
                    # 2. Assets extension
                    if "assets" in variant_props:
                        assets_def = variant_props["assets"]
                        if "additionalProperties" in assets_def:
                            template["assets"]["*"] = self._parse_field(assets_def["additionalProperties"], schema)
                        elif "properties" in assets_def:
                            # Merge properties into a single template for all assets
                            assets_template = {}
                            for key, prop_def in assets_def["properties"].items():
                                assets_template[key] = self._parse_field(prop_def, schema)
                            if assets_template:
                                template["assets"]["*"] = assets_template
                    break
        
        # Cleanup empty fields
        if not template["properties"]:
            template.pop("properties", None)
        if not template["assets"]:
            template.pop("assets", None)
            
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
        item_id = item.get("id", "unknown")
        
        # DEBUG: Processing item
        self.logger.debug(f"Processing item | item: {item_id}")
        
        fields_scaffolded = 0
        defaults_applied = 0
        
        # 1. Tag extension
        if "stac_extensions" not in item:
            item["stac_extensions"] = []
        
        extension_added = False
        if self.config.schema_uri not in item["stac_extensions"]:
            item["stac_extensions"].append(self.config.schema_uri)
            extension_added = True
            self.logger.debug(f"Added extension URI | item: {item_id} | uri: {self.config.schema_uri}")
        
        # 2. Apply properties template
        if "properties" in self.template:
            prop_count = len(self.template["properties"])
            item["properties"] = deep_merge(
                item.get("properties", {}), 
                self.template["properties"], 
                strategy='keep_existing'
            )
            fields_scaffolded += prop_count
            self.logger.debug(f"Scaffolded properties | item: {item_id} | fields: {prop_count}")
        
        # 3. Apply assets template (with user defaults)
        if "assets" in self.template:
            asset_template = self.template["assets"].get("*") or {}
            
            # Ensure at least one asset exists if requested by user pattern
            if "assets" not in item or not item["assets"]:
                # Create a default asset using pystac
                default_asset = pystac.Asset(href="Asset reference", title="Asset title")
                item["assets"] = {"AssetId": default_asset.to_dict()}
                self.logger.debug(f"Created default asset | item: {item_id}")
            
            # Extend all assets with the template
            asset_count = len(item["assets"])
            for asset_key in item["assets"]:
                item["assets"][asset_key] = deep_merge(
                    item["assets"][asset_key],
                    asset_template,
                    strategy='keep_existing'
                )
            
            if asset_template:
                template_fields = len(asset_template)
                fields_scaffolded += template_fields * asset_count
                self.logger.debug(
                    f"Scaffolded assets | item: {item_id} | assets: {asset_count} | "
                    f"fields_per_asset: {template_fields}"
                )
        
        # 4. Expand and apply wildcard defaults (per-item, supports template variables)
        # Only expand defaults that contain wildcards or dot-notation paths
        if self.raw_defaults:
            # Filter to only wildcard or dot-notation defaults (exclude nested dict defaults)
            expandable_defaults = {
                k: v for k, v in self.raw_defaults.items() 
                if "*" in k or "." in k
            }
            
            if expandable_defaults:
                # Expand wildcards to actual paths in this item
                expanded_defaults = expand_wildcard_paths(
                    expandable_defaults,
                    item,
                    context={
                        "item_id": item.get("id"),
                        "collection_id": item.get("collection")
                    }
                )
                
                # Apply each expanded path individually to preserve unique values per asset
                if expanded_defaults:
                    from stac_manager.utils.field_ops import set_nested_field
                    for path, value in expanded_defaults.items():
                        set_nested_field(item, path, value)
                        defaults_applied += 1
                        self.logger.debug(
                            f"Applied default | item: {item_id} | path: {path} | value: {value}"
                        )
        
        # INFO: Summary of extension application
        self.logger.info(
            f"Applied extension | item: {item_id} | uri: {self.config.schema_uri} | "
            f"fields_scaffolded: {fields_scaffolded} | defaults_applied: {defaults_applied}"
        )
        
        return item

