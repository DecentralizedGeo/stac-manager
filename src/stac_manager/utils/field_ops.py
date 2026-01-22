"""Field manipulation utilities for STAC items."""
from typing import Any


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
