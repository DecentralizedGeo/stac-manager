import pytest
from stac_manager.modules.update import UpdateModule
from tests.fixtures.context import MockWorkflowContext
from tests.fixtures.stac_items import VALID_ITEM


def test_update_module_sets_field():
    """UpdateModule sets top-level field."""
    module = UpdateModule({
        "updates": {"properties.license": "CC-BY-4.0"}
    })
    context = MockWorkflowContext.create()
    
    item = VALID_ITEM.copy()
    result = module.modify(item, context)
    
    assert result["properties"]["license"] == "CC-BY-4.0"
    assert result["properties"]["datetime"] == "2024-01-01T00:00:00Z"  # Unchanged


def test_update_module_creates_nested_paths():
    """UpdateModule creates missing intermediate paths."""
    module = UpdateModule({
        "updates": {"properties.custom:metadata.depth.value": 42},
        "create_missing_paths": True
    })
    context = MockWorkflowContext.create()
    
    item = VALID_ITEM.copy()
    result = module.modify(item, context)
    
    assert result["properties"]["custom:metadata"]["depth"]["value"] == 42


def test_update_module_removes_field():
    """UpdateModule removes specified fields."""
    module = UpdateModule({
        "removes": ["properties.deprecated_field"]
    })
    context = MockWorkflowContext.create()
    
    item = VALID_ITEM.copy()
    item["properties"]["deprecated_field"] = "value"
    
    result = module.modify(item, context)
    
    assert "deprecated_field" not in result["properties"]


def test_update_module_updates_timestamp():
    """UpdateModule updates properties.updated by default."""
    module = UpdateModule({})
    context = MockWorkflowContext.create()
    
    item = VALID_ITEM.copy()
    item["properties"]["updated"] = "2023-01-01T00:00:00Z"
    original_updated = item["properties"]["updated"]
    
    # Mock datetime to ensure change or just check inequality if we can't easily mock
    # For now, just check it changed or exists
    result = module.modify(item, context)
    
    assert result["properties"]["updated"] != original_updated
    # Ideally check format 2024-...


import tempfile
import json


def test_update_module_applies_patch_file():
    """UpdateModule applies patch from file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        # Patch is now keyed by item ID
        json.dump({
            "test-item-001": {"properties": {"patch_applied": True}}
        }, f)
        patch_path = f.name
    
    try:
        module = UpdateModule({
            "patch_file": patch_path,
            "mode": "merge"
        })
        context = MockWorkflowContext.create()
        
        item = VALID_ITEM.copy()
        # Ensure item knows its ID (VALID_ITEM usually has id='test-item-001')
        
        result = module.modify(item, context)
        
        assert result["properties"]["patch_applied"] is True
    finally:
        import os
        os.unlink(patch_path)


from stac_manager.exceptions import DataProcessingError


def test_update_module_path_collision_error():
    """UpdateModule raises error on path collision."""
    module = UpdateModule({
        "updates": {"properties.datetime.invalid": "value"}
    })
    context = MockWorkflowContext.create()
    
    item = VALID_ITEM.copy()
    # datetime is a string, can't traverse it
    
    with pytest.raises(DataProcessingError) as exc_info:
        module.modify(item, context)
    
    
    assert "Cannot traverse non-dict" in str(exc_info.value)


from stac_manager.protocols import Modifier


def test_update_module_protocols():
    """UpdateModule implements Modifier protocol."""
    # module = UpdateModule({})
    module = UpdateModule({"updates": {"properties.test": "value"}})

    assert isinstance(module, Modifier)







def test_update_module_applies_patch_file_update_only(tmp_path):
    """Test applying patches from a file in update_only mode."""
    # Create patch file
    patches = {
        "test-item-001": {
            "properties": {
                "title": "Patched Title",  # Should update
                "new_field": "Should Not Exist"  # Should be ignored (new key)
            }
        }
    }
    patch_file = tmp_path / "patches.json"
    with open(patch_file, "w") as f:
        json.dump(patches, f)
        
    config = {
        "patch_file": str(patch_file),
        "mode": "update_only",
        "auto_update_timestamp": False
    }
    
    module = UpdateModule(config)
    
    item = VALID_ITEM.copy()
    # VALID_ITEM usually has "title" in properties? if not, we should set it to test logic.
    item["properties"]["title"] = "Original Title"
    
    result = module.modify(item, None)
    
    assert result["properties"]["title"] == "Patched Title"
    assert "new_field" not in result["properties"]
