"""Geometry utilities for STAC items."""
from typing import Any
from shapely.geometry import shape, mapping
from shapely.validation import make_valid


def ensure_bbox(geometry: dict | None) -> list[float] | None:
    """
    Calculate bounding box for a GeoJSON geometry.
    
    Args:
        geometry: GeoJSON geometry dict or None
        
    Returns:
        [minx, miny, maxx, maxy] or None
    """
    if geometry is None:
        return None
        
    s = shape(geometry)
    return list(s.bounds)


def validate_and_repair_geometry(geometry: dict) -> dict:
    """
    Validate and repair GeoJSON geometry using Shapely.
    
    Args:
        geometry: GeoJSON geometry dict
        
    Returns:
        Repaired GeoJSON geometry dict (nested lists for coordinates)
    """
    s = shape(geometry)
    if not s.is_valid:
        s = make_valid(s)
    
    mapped = mapping(s)
    
    # Recursively convert tuples to lists
    def _to_list(obj: Any) -> Any:
        if isinstance(obj, tuple):
            return [_to_list(x) for x in obj]
        if isinstance(obj, list):
            return [_to_list(x) for x in obj]
        return obj

    return {
        "type": mapped["type"],
        "coordinates": _to_list(mapped["coordinates"])
    }


