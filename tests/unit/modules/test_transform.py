import pytest
import tempfile
import json
import os
from stac_manager.modules.transform import TransformModule
from tests.fixtures.context import MockWorkflowContext


def test_transform_module_loads_json_input():
    """TransformModule loads JSON input file."""
    input_data = [
        {"id": "item-001", "custom_field": "value1"},
        {"id": "item-002", "custom_field": "value2"}
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(input_data, f)
        temp_path = f.name
    
    try:
        module = TransformModule({
            "input_file": temp_path,
            "field_mapping": {"properties.custom": "custom_field"}
        })
        
        assert module.sidecar_index is not None
        assert "item-001" in module.sidecar_index
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_transform_module_indexes_dict_input():
    """TransformModule treats dict keys as IDs."""
    input_data = {
        "item-001": {"custom_field": "value1"},
        "item-002": {"custom_field": "value2"}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(input_data, f)
        temp_path = f.name
    
    try:
        module = TransformModule({
            "input_file": temp_path,
            "field_mapping": {"properties.custom": "custom_field"}
        })
        
        assert "item-001" in module.sidecar_index
        assert module.sidecar_index["item-001"]["custom_field"] == "value1"
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def test_transform_module_indexes_list_input():
    """TransformModule extracts IDs from list using JMESPath/Key."""
    input_data = [
        {"item_id": "item-001", "custom_field": "value1"},
        {"item_id": "item-002", "custom_field": "value2"}
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(input_data, f)
        temp_path = f.name
    
    try:
        module = TransformModule({
            "input_file": temp_path,
            "input_join_key": "item_id",
            "field_mapping": {"properties.custom": "custom_field"}
        })
        
        assert "item-001" in module.sidecar_index
        assert module.sidecar_index["item-001"]["custom_field"] == "value1"
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_transform_module_enrich_explicit_mapping():
    """TransformModule enriches item using explicit field mapping."""
    input_data = {
        "item-001": {"new_field": "val1", "existing_field": "sidecar_val"}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(input_data, f)
        temp_path = f.name
    
    try:
        module = TransformModule({
            "input_file": temp_path,
            "field_mapping": {
                "properties.new_field": "new_field",
                # Note: "existing_field" not mapped, so it shouldn't touch existing property
            }
        })
        
        item = {
            "id": "item-001",
            "properties": {"existing_field": "original_val"}
        }
        context = MockWorkflowContext.create()
        
        result = module.modify(item, context)
        
        # New field should be added
        assert result["properties"]["new_field"] == "val1"
        # Existing field should NOT be overwritten (not mapped)
        assert result["properties"]["existing_field"] == "original_val"
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_transform_module_enrich_overwrite():
    """TransformModule overwrites existing fields when mapped."""
    input_data = {
        "item-001": {"existing_field": "sidecar_val"}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(input_data, f)
        temp_path = f.name
    
    try:
        module = TransformModule({
            "input_file": temp_path,
            "field_mapping": {
                "properties.existing_field": "existing_field"
            }
        })
        
        item = {
            "id": "item-001",
            "properties": {"existing_field": "original_val"}
        }
        context = MockWorkflowContext.create()
        
        result = module.modify(item, context)
        
        # Existing field SHOULD be overwritten
        assert result["properties"]["existing_field"] == "sidecar_val"
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_transform_module_field_mapping_custom_target():
    """TransformModule maps input fields to arbitrary target struct."""
    input_data = {
        "item-001": {"raw_score": 0.95, "other": "data"}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(input_data, f)
        temp_path = f.name
    
    try:
        module = TransformModule({
            "input_file": temp_path,
            "field_mapping": {
                "properties.analysis.score": "raw_score"
            }
        })
        
        item = {"id": "item-001", "properties": {}}
        context = MockWorkflowContext.create()
        
        result = module.modify(item, context)
        
        # Mapped field should exist in nested structure
        assert result["properties"]["analysis"]["score"] == 0.95
        assert "other" not in result["properties"]
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_transform_module_missing_item_handling():
    """TransformModule handles missing items based on config."""
    input_data = {"item-001": {"score": 0.95}}
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(input_data, f)
        temp_path = f.name
    
    try:
        # 1. Ignore (default)
        module = TransformModule({
            "input_file": temp_path, 
            "handle_missing": "ignore",
            "field_mapping": {"properties.score": "score"}
        })
        item = {"id": "missing-item", "properties": {}}
        context = MockWorkflowContext.create()
        result = module.modify(item.copy(), context)
        assert result == item # No change
        
        # 2. Error
        module_error = TransformModule({
            "input_file": temp_path, 
            "handle_missing": "error",
            "field_mapping": {"properties.score": "score"}
        })
        from stac_manager.exceptions import DataProcessingError
        with pytest.raises(DataProcessingError):
            module_error.modify(item.copy(), context)
            
        # 3. Warn
        module_warn = TransformModule({
            "input_file": temp_path, 
            "handle_missing": "warn",
            "field_mapping": {"properties.score": "score"}
        })
        module_warn.modify(item.copy(), context)
        # Check if warning was collected
        failures = context.failure_collector.get_all()
        assert len(failures) > 0
        assert "Missing sidecar data" in failures[0].message
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_transform_module_implements_modifier_protocol():
    """TransformModule implements the Modifier protocol."""
    from stac_manager.protocols import Modifier
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({}, f)
        temp_path = f.name
        
    try:
        module = TransformModule({
            "input_file": temp_path,
            "field_mapping": {"a": "b"}
        })
        assert isinstance(module, Modifier)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
