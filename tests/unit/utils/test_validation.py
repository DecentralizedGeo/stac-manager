import pytest
from stac_manager.utils.validation import validate_stac_item, validate_schema
from tests.fixtures.stac_items import VALID_ITEM, PARTIAL_ITEM


def test_validate_stac_item_valid():
    """validate_stac_item returns True for valid item."""
    # Note: stac-validator usually returns a dict/object, we want to know if valid
    is_valid, errors = validate_stac_item(VALID_ITEM)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_stac_item_invalid():
    """validate_stac_item returns False and errors for invalid item."""
    invalid_item = PARTIAL_ITEM.copy()
    invalid_item.pop("stac_version", None)  # Required field
    
    is_valid, errors = validate_stac_item(invalid_item)
    assert is_valid is False
    assert len(errors) > 0


def test_validate_schema_valid():
    """validate_schema returns True for valid data."""
    schema = {
        "type": "object",
        "properties": {"id": {"type": "string"}},
        "required": ["id"]
    }
    data = {"id": "test"}
    is_valid, errors = validate_schema(data, schema)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_schema_invalid():
    """validate_schema returns False and errors for invalid data."""
    schema = {
        "type": "object",
        "properties": {"id": {"type": "string"}},
        "required": ["id"]
    }
    data = {"id": 123}  # Wrong type
    is_valid, errors = validate_schema(data, schema)
    assert is_valid is False
    assert len(errors) > 0
