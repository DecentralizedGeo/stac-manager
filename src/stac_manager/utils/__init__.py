"""STAC Manager foundation utilities."""
from stac_manager.utils.serialization import ensure_dict, from_dict
from stac_manager.utils.field_ops import (
    set_nested_field,
    get_nested_field,
    deep_merge,
    apply_jmespath,
)
from stac_manager.utils.geometry import (
    ensure_bbox,
    validate_and_repair_geometry,
)
from stac_manager.utils.streaming import chunk_stream, limit_stream
from stac_manager.utils.validation import validate_stac_item, validate_schema

__all__ = [
    "ensure_dict",
    "from_dict",
    "set_nested_field",
    "get_nested_field",
    "deep_merge",
    "apply_jmespath",
    "ensure_bbox",
    "validate_and_repair_geometry",
    "chunk_stream",
    "limit_stream",
    "validate_stac_item",
    "validate_schema",
]
