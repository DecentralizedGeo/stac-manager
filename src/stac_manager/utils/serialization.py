"""PySTAC ↔ dict serialization utilities."""
from typing import Union
import pystac


def ensure_dict(obj: Union[dict, pystac.STACObject]) -> dict:
    """
    Ensure input is a dict.
    
    Args:
        obj: dict or PySTAC object
        
    Returns:
        dict representation
    """
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, pystac.STACObject):
        return obj.to_dict()
    raise TypeError(f"Expected dict or PySTAC object, got {type(obj)}")


def from_dict(
    d: dict, 
    stac_type: str | None = None
) -> pystac.STACObject:
    """
    Create PySTAC object from dict with auto-detection.
    
    Args:
        d: STAC dict
        stac_type: Optional type hint ('Item', 'Collection', 'Catalog')
        
    Returns:
        PySTAC object
    """
    if stac_type == 'Item':
        return pystac.Item.from_dict(d)
    elif stac_type == 'Collection':
        return pystac.Collection.from_dict(d)
    elif stac_type == 'Catalog':
        return pystac.Catalog.from_dict(d)
    else:
        # Auto-detect
        return pystac.read_dict(d)
