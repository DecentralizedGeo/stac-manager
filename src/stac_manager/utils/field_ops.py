"""Field manipulation utilities for STAC items."""
from typing import Any, Literal
import jmespath
import copy
from stac_manager.exceptions import DataProcessingError


def set_nested_field(item: dict, path: str, value: Any) -> None:
    """
    Set nested field using dot notation.
    Creates intermediate dicts as needed.
    
    Args:
        item: STAC item dict (modified in-place)
        path: Dot-separated path (e.g., "properties.eo:cloud_cover")
        value: Value to set
    """
    keys = path.split('.')
    current = item
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value


def get_nested_field(item: dict, path: str, default: Any = None) -> Any:
    """
    Get nested field value using dot notation.
    
    Args:
        item: STAC item dict
        path: Dot-separated path
        default: Default value if path doesn't exist
        
    Returns:
        Field value or default
    """
    keys = path.split('.')
    current = item
    
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    
    return current


def deep_merge(
    base: dict,
    overlay: dict,
    strategy: Literal['keep_existing', 'overwrite', 'update_only'] = 'overwrite'
) -> dict:
    """
    Recursively merge two dictionaries.
    
    Args:
        base: Base dictionary (modified in-place)
        overlay: Dictionary to merge into base
        strategy: Merge strategy ('keep_existing', 'overwrite', 'update_only')
        
    Returns:
        Merged dictionary (same object as base)
    """
    for key, value in overlay.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            # Both are dicts - recurse
            deep_merge(base[key], value, strategy)
        elif key not in base:
            # New key - add unless strategy is 'update_only'
            if strategy != 'update_only':
                # Deep copy to avoid sharing dict objects across multiple assets
                base[key] = copy.deepcopy(value)
        elif strategy != 'keep_existing':
            # Key exists - overwrite if strategy is 'overwrite' or 'update_only'
            base[key] = copy.deepcopy(value)
        # else: keep_existing - don't modify base[key]
    
    return base


def apply_jmespath(item: dict, query: str) -> Any:
    """
    Apply JMESPath query to item.
    
    Args:
        item: STAC item dict
        query: JMESPath query string
        
    Returns:
        Query result
        
    Raises:
        DataProcessingError: If query is invalid
    """
    try:
        return jmespath.search(query, item)
    except Exception as e:
        raise DataProcessingError(f"JMESPath query failed: {e}")


def expand_wildcard_paths(
    template_dict: dict,
    target_item: dict,
    context: dict | None = None
) -> dict:
    """
    Expand wildcard paths in template dict to match actual keys in target item.
    
    Supports:
    - Wildcards: assets.*.field matches all keys in assets
    - Template variables: {item_id}, {collection_id}, {asset_key}
    
    Args:
        template_dict: Dict with potentially wildcarded paths as keys
        target_item: STAC item to match wildcards against
        context: Optional context for template variables (item_id, collection_id)
        
    Returns:
        New dict with expanded paths (wildcards replaced with actual keys)
        
    Example:
        template_dict = {
            "assets.*.alternate.s3.href": "s3://bucket/{asset_key}/",
            "assets.visual.title": "Visual Image"
        }
        target_item = {"assets": {"visual": {...}, "B04": {...}}}
        
        Returns:
        {
            "assets.visual.alternate.s3.href": "s3://bucket/visual/",
            "assets.B04.alternate.s3.href": "s3://bucket/B04/",
            "assets.visual.title": "Visual Image"
        }
    """
    if context is None:
        context = {}
    
    # Add item context if available
    if "item_id" not in context and "id" in target_item:
        context["item_id"] = target_item["id"]
    if "collection_id" not in context and "collection" in target_item:
        context["collection_id"] = target_item["collection"]
    
    expanded = {}
    
    for path, value in template_dict.items():
        if "*" not in path:
            # No wildcard - apply template variables and keep as-is
            expanded_value = _apply_template_variables(value, context)
            expanded[path] = expanded_value
            continue
        
        # Parse path to find wildcard position
        parts = path.split(".")
        wildcard_idx = parts.index("*")
        
        # Get the parent path (before wildcard)
        parent_path = ".".join(parts[:wildcard_idx]) if wildcard_idx > 0 else ""
        
        # Get parent object from target item
        parent_obj = get_nested_field(target_item, parent_path, {}) if parent_path else target_item
        
        if not isinstance(parent_obj, dict):
            continue
        
        # Expand wildcard to all keys in parent object
        suffix = ".".join(parts[wildcard_idx + 1:]) if wildcard_idx < len(parts) - 1 else ""
        
        for key in parent_obj.keys():
            # Build expanded path
            if parent_path:
                expanded_path = f"{parent_path}.{key}"
            else:
                expanded_path = key
            
            if suffix:
                expanded_path = f"{expanded_path}.{suffix}"
            
            # Apply template variables with asset_key context (create new dict to avoid mutation)
            asset_context = dict(context) if context else {}
            asset_context["asset_key"] = key
            expanded_value = _apply_template_variables(value, asset_context)
            
            expanded[expanded_path] = expanded_value
    
    return expanded


def _apply_template_variables(value: Any, context: dict) -> Any:
    """
    Apply template variable substitution to a value.
    
    Supports:
    - {item_id}: Item ID
    - {collection_id}: Collection ID
    - {asset_key}: Asset key (only in asset context)
    
    Args:
        value: Value to process (strings are substituted, others returned as-is)
        context: Dict with variable values
        
    Returns:
        Value with variables substituted
    """
    if not isinstance(value, str):
        return value
    
    result = value
    for var_name, var_value in context.items():
        placeholder = f"{{{var_name}}}"
        if placeholder in result:
            result = result.replace(placeholder, str(var_value))
    
    return result
