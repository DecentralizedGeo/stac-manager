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
