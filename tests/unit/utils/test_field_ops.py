import pytest
from stac_manager.utils.field_ops import set_nested_field, get_nested_field
from tests.fixtures.stac_items import VALID_ITEM


def test_set_nested_field_simple():
    """set_nested_field sets top-level field."""
    item = VALID_ITEM.copy()
    set_nested_field(item, "id", "new-id")
    
    assert item["id"] == "new-id"


def test_set_nested_field_two_levels():
    """set_nested_field creates and sets nested field."""
    item = VALID_ITEM.copy()
    set_nested_field(item, "properties.platform", "Landsat-8")
    
    assert item["properties"]["platform"] == "Landsat-8"
    assert item["properties"]["datetime"] == "2024-01-01T00:00:00Z"  # Unchanged


def test_get_nested_field_exists():
    """get_nested_field retrieves existing nested value."""
    result = get_nested_field(VALID_ITEM, "properties.datetime")
    assert result == "2024-01-01T00:00:00Z"


def test_get_nested_field_missing_with_default():
    """get_nested_field returns default when path missing."""
    result = get_nested_field(VALID_ITEM, "properties.missing", default="N/A")
    assert result == "N/A"


def test_get_nested_field_missing_no_default():
    """get_nested_field returns None when path missing and no default."""
    result = get_nested_field(VALID_ITEM, "properties.missing")
    assert result is None
