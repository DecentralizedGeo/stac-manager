"""Field manipulation utilities for STAC items."""
from typing import Any, Literal


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
    strategy: Literal['keep_existing', 'overwrite'] = 'overwrite'
) -> dict:
    """
    Recursively merge two dictionaries.
    
    Args:
        base: Base dictionary (modified in-place)
        overlay: Dictionary to merge into base
        strategy: Merge strategy ('overwrite' or 'keep_existing')
        
    Returns:
        Merged dictionary (same object as base)
    """
    for key, value in overlay.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            # Both are dicts - recurse
            deep_merge(base[key], value, strategy)
        elif key not in base:
            # New key - always add
            base[key] = value
        elif strategy == 'overwrite':
            # Key exists, overwrite
            base[key] = value
        # else: keep_existing - don't modify base[key]
    
    return base
