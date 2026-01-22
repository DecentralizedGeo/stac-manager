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
