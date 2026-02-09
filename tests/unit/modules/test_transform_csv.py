import pytest
import tempfile
import os
import csv
import json
from stac_manager.modules.transform import TransformModule
from stac_manager.exceptions import DataProcessingError
from tests.fixtures.context import MockWorkflowContext

def test_transform_csv_inference_and_id_safety():
    """Verify CSV loading with auto-inference and ID column safety."""
    # "007" would be inferred as 7 (int) if not protected
    # "10.5" should be inferred as float
    # "2023-01-01" might be timestamp or string depending on pyarrow
    rows = [
        {"id": "007", "cloud_cover": "10.5", "date": "2023-01-01", "name": "Bond"}
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        temp_path = f.name
        
    try:
        module = TransformModule({
            "input_file": temp_path,
            "input_join_key": "id",
            "field_mapping": {
                "properties.eo:cloud_cover": "cloud_cover",
                "properties.name": "name"
            },
            "strategy": "merge"  # Create new properties
        })
        
        # Test ID indexing (should find "007" as string)
        assert "007" in module.input_index
        entry = module.input_index["007"]
        
        # Verify type inference
        # cloud_cover should be float
        assert isinstance(entry["cloud_cover"], float)
        assert entry["cloud_cover"] == 10.5
        
        # Verify ID safety (should be string "007", not int 7)
        assert isinstance(entry["id"], str)
        assert entry["id"] == "007"
        
        # Verify Modify
        item = {"id": "007", "properties": {}}
        context = MockWorkflowContext.create()
        result = module.modify(item, context)
        
        assert result["properties"]["eo:cloud_cover"] == 10.5
        
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def test_transform_hybrid_field_mapping():
    """Verify Hybrid Field Mapping (Simple Key + JMESPath)."""
    # JSON input with complex structure
    input_data = {
        "item-001": {
            "simple_field": "simple",
            "Field With Spaces": "spaced value",
            "complex": {
                "list": [{"attr": "val1"}, {"attr": "val2"}]
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(input_data, f)
        temp_path = f.name
        
    try:
        module = TransformModule({
            "input_file": temp_path,
            "field_mapping": {
                # Simple key with spaces (Direct lookup)
                "properties.spaced": "Field With Spaces",
                # JMESPath extraction
                "properties.extracted": "complex.list[0].attr",
                # Nested target creation
                "properties.meta.info": "simple_field"
            },
            "strategy": "merge"  # Create new properties
        })
        
        item = {"id": "item-001", "properties": {}}
        context = MockWorkflowContext.create()
        result = module.modify(item, context)
        
        assert result["properties"]["spaced"] == "spaced value"
        assert result["properties"]["extracted"] == "val1"
        assert result["properties"]["meta"]["info"] == "simple"
        
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def test_transform_nested_object_mapping():
    """Verify mapping an entire object/list to a property."""
    input_data = {
        "item-001": {
            "telemetry": {
                "sensors": [{"id": "s1", "gain": 1.0}]
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(input_data, f)
        temp_path = f.name
        
    try:
        module = TransformModule({
            "input_file": temp_path,
            "field_mapping": {
                # Map list object to property
                "properties.instruments": "telemetry.sensors"
            },
            "strategy": "merge"  # Create new property
        })
        
        item = {"id": "item-001", "properties": {}}
        context = MockWorkflowContext.create()
        result = module.modify(item, context)
        
        # Should be list of dicts
        assert isinstance(result["properties"]["instruments"], list)
        assert result["properties"]["instruments"][0]["id"] == "s1"
        assert result["properties"]["instruments"][0]["gain"] == 1.0
        
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
