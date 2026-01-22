import pytest
from stac_manager.utils.field_ops import set_nested_field, get_nested_field, deep_merge, apply_jmespath
from tests.fixtures.stac_items import VALID_ITEM, NESTED_ITEM


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


def test_deep_merge_overwrite_strategy():
    """deep_merge with overwrite strategy replaces values."""
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    overlay = {"b": {"c": 99, "e": 4}, "f": 5}
    
    result = deep_merge(base, overlay, strategy='overwrite')
    
    assert result["a"] == 1  # Unchanged
    assert result["b"]["c"] == 99  # Overwritten
    assert result["b"]["d"] == 3  # Unchanged
    assert result["b"]["e"] == 4  # Added
    assert result["f"] == 5  # Added


def test_deep_merge_keep_existing_strategy():
    """deep_merge with keep_existing preserves base values."""
    base = {"a": 1, "b": {"c": 2}}
    overlay = {"a": 99, "b": {"c": 99, "d": 4}}
    
    result = deep_merge(base, overlay, strategy='keep_existing')
    
    assert result["a"] == 1  # Kept (not overwritten)
    assert result["b"]["c"] == 2  # Kept
    assert result["b"]["d"] == 4  # Added (new key)


def test_apply_jmespath_simple_path():
    """apply_jmespath extracts value with simple path."""
    result = apply_jmespath(NESTED_ITEM, "id")
    assert result == "nested-001"


def test_apply_jmespath_nested_path():
    """apply_jmespath extracts nested value."""
    result = apply_jmespath(NESTED_ITEM, "properties.\"eo:cloud_cover\"")
    assert result == 15.5


def test_apply_jmespath_array_filter():
    """apply_jmespath filters array."""
    result = apply_jmespath(NESTED_ITEM, "properties.instruments[0]")
    assert result == "OLI"
