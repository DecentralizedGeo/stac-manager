import pytest
from stac_manager.modules.validate import ValidateModule
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
    assert len(context.failure_collector.failures) == 1
    assert "validation" in context.failure_collector.failures[0]["error"].lower()
