import pytest
from stac_manager.utils.field_ops import (
    set_nested_field, get_nested_field, deep_merge, apply_jmespath,
    expand_wildcard_removal_paths
)
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


def test_expand_wildcard_removal_paths_no_wildcard():
    """expand_wildcard_removal_paths returns simple path as tuple."""
    paths = ["properties.deprecated_field"]
    item = {"properties": {"deprecated_field": "value", "other": "data"}}
    
    result = expand_wildcard_removal_paths(paths, item)
    
    assert result == [("properties", "deprecated_field")]


def test_expand_wildcard_removal_paths_single_wildcard():
    """expand_wildcard_removal_paths expands wildcard to all matching keys."""
    paths = ["assets.*.alternate"]
    item = {
        "assets": {
            "blue": {"href": "s3://...", "alternate": {"ipfs": {}}},
            "red": {"href": "s3://...", "alternate": {"filecoin": {}}},
            "metadata": {"href": "s3://..."}  # No alternate field
        }
    }
    
    result = expand_wildcard_removal_paths(paths, item)
    
    # Should expand to all asset keys (even if alternate doesn't exist)
    assert len(result) == 3
    assert ("assets", "blue", "alternate") in result
    assert ("assets", "red", "alternate") in result
    assert ("assets", "metadata", "alternate") in result


def test_expand_wildcard_removal_paths_multiple_paths():
    """expand_wildcard_removal_paths handles multiple removal paths."""
    paths = ["assets.*.alternate", "properties.old_field"]
    item = {
        "assets": {
            "visual": {"alternate": {}},
            "B04": {"alternate": {}}
        },
        "properties": {"old_field": "value"}
    }
    
    result = expand_wildcard_removal_paths(paths, item)
    
    assert len(result) == 3
    assert ("assets", "visual", "alternate") in result
    assert ("assets", "B04", "alternate") in result
    assert ("properties", "old_field") in result


def test_expand_wildcard_removal_paths_nested_wildcard():
    """expand_wildcard_removal_paths handles nested paths after wildcard."""
    paths = ["assets.*.alternate.ipfs"]
    item = {
        "assets": {
            "blue": {"alternate": {"ipfs": {}, "s3": {}}},
            "red": {"alternate": {"ipfs": {}}}
        }
    }
    
    result = expand_wildcard_removal_paths(paths, item)
    
    assert len(result) == 2
    assert ("assets", "blue", "alternate", "ipfs") in result
    assert ("assets", "red", "alternate", "ipfs") in result

