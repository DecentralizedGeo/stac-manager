import pytest
from stac_manager.modules.validate import ValidateModule
from stac_manager.exceptions import DataProcessingError
from stac_manager.protocols import Modifier
from tests.fixtures.context import MockWorkflowContext
from tests.fixtures.stac_items import VALID_ITEM


def test_validate_module_passes_valid_item():
    """ValidateModule passes valid STAC items."""
    module = ValidateModule({"strict": False})
    context = MockWorkflowContext.create()
    
    result = module.modify(VALID_ITEM.copy(), context)
    
    assert result is not None
    assert result["id"] == "test-item-001"


def test_validate_module_rejects_invalid_item():
    """ValidateModule returns None for invalid items in permissive mode."""
    module = ValidateModule({"strict": False})
    context = MockWorkflowContext.create()
    
    invalid_item = {"id": "test"}  # Missing required STAC fields
    
    result = module.modify(invalid_item, context)
    
    assert result is None
    failures = context.failure_collector.get_all()
    assert len(failures) == 1
    assert "validation" in failures[0].message.lower()


def test_validate_module_strict_mode_raises():
    """ValidateModule raises error for invalid items in strict mode."""
    module = ValidateModule({"strict": True})
    context = MockWorkflowContext.create()
    
    invalid_item = {"id": "test"}
    
    with pytest.raises(DataProcessingError) as exc_info:
        module.modify(invalid_item, context)
    
    assert "validation failed" in str(exc_info.value).lower()


def test_validate_module_with_extension_schemas():
    """ValidateModule validates against extension schemas."""
    module = ValidateModule({
        "extension_schemas": ["https://stac-extensions.github.io/eo/v1.1.0/schema.json"]
    })
    context = MockWorkflowContext.create()
    
    item = VALID_ITEM.copy()
    item["stac_extensions"] = ["https://stac-extensions.github.io/eo/v1.1.0/schema.json"]
    item["properties"]["eo:cloud_cover"] = 15.5
    
    result = module.modify(item, context)
    
    assert result is not None


def test_validate_module_implements_modifier_protocol():
    """ValidateModule implements Modifier protocol."""
    module = ValidateModule({})
    assert isinstance(module, Modifier)
