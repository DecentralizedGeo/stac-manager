"""Tests for pattern-based field mapping in TransformModule."""
import pytest
import json
from pathlib import Path
from stac_manager.modules.transform import TransformModule
from tests.fixtures.context import MockWorkflowContext
import logging


@pytest.fixture
def temp_input_file(tmp_path):
    """Create temporary input file with asset data."""
    input_file = tmp_path / "assets.json"
    data = {
        "item-1": {
            "assets": {
                "blue": {"cid": "QmBlue123", "size": 1000},
                "green": {"cid": "QmGreen456", "size": 2000},
                "red": {"cid": "QmRed789", "size": 3000}
            }
        }
    }
    input_file.write_text(json.dumps(data))
    return input_file


def test_wildcard_expansion_with_merge_strategy(temp_input_file):
    """Wildcards should expand to all assets in input data with merge strategy."""
    config = {
        "input_file": str(temp_input_file),
        "field_mapping": {
            "assets.*.dgeo:cid": "assets.{asset_key}.cid",
            "assets.*.dgeo:size": "assets.{asset_key}.size"
        },
        "strategy": "merge"
    }
    
    module = TransformModule(config)
    
    item = {
        "id": "item-1",
        "assets": {
            "blue": {"href": "s3://blue.tif"},
            "green": {"href": "s3://green.tif"}
            # Note: no "red" asset in item yet
        }
    }
    
    context = MockWorkflowContext.create()
    result = module.modify(item, context)
    
    # Should update existing assets with wildcard expansion
    assert result["assets"]["blue"]["dgeo:cid"] == "QmBlue123"
    assert result["assets"]["blue"]["dgeo:size"] == 1000
    assert result["assets"]["green"]["dgeo:cid"] == "QmGreen456"
    assert result["assets"]["green"]["dgeo:size"] == 2000
    
    # Note: Wildcards expand against item structure (blue, green), 
    # not input structure. "red" asset won't be created even with merge strategy
    # because the wildcard pattern only matches existing item assets.
    assert "red" not in result["assets"]


def test_update_existing_strategy_filtering(temp_input_file):
    """update_existing strategy should only update paths that already exist."""
    config = {
        "input_file": str(temp_input_file),
        "field_mapping": {
            "assets.*.dgeo:cid": "assets.{asset_key}.cid",  # Won't apply (doesn't exist)
            "assets.*.href": "assets.{asset_key}.size"  # Will apply (exists)
        },
        "strategy": "update_existing"
    }
    
    module = TransformModule(config)
    
    item = {
        "id": "item-1",
        "assets": {
            "blue": {"href": "s3://blue.tif"},
            "green": {"href": "s3://green.tif"}
        }
    }
    
    context = MockWorkflowContext.create()
    result = module.modify(item, context)
    
    # Should update existing field (href)
    assert result["assets"]["blue"]["href"] == 1000  # Size from input
    assert result["assets"]["green"]["href"] == 2000
    
    # Should NOT create new field (dgeo:cid) because it doesn't exist
    assert "dgeo:cid" not in result["assets"]["blue"]
    assert "dgeo:cid" not in result["assets"]["green"]


def test_template_variable_in_jmespath(temp_input_file):
    """Template variables in JMESPath queries should substitute correctly."""
    config = {
        "input_file": str(temp_input_file),
        "field_mapping": {
            # Template variable {asset_key} in JMESPath query
            "assets.*.dgeo:cid": "assets.{asset_key}.cid",
            "assets.*.dgeo:size": "assets.{asset_key}.size"
        },
        "strategy": "merge"
    }
    
    module = TransformModule(config)
    
    item = {
        "id": "item-1",
        "assets": {
            "blue": {"href": "s3://blue.tif"},
            "green": {"href": "s3://green.tif"}
        }
    }
    
    context = MockWorkflowContext.create()
    result = module.modify(item, context)
    
    # For blue: assets.{asset_key}.cid becomes assets.blue.cid (from input)
    assert result["assets"]["blue"]["dgeo:cid"] == "QmBlue123"
    assert result["assets"]["blue"]["dgeo:size"] == 1000
    
    # For green: assets.{asset_key}.cid becomes assets.green.cid (from input)
    assert result["assets"]["green"]["dgeo:cid"] == "QmGreen456"
    assert result["assets"]["green"]["dgeo:size"] == 2000
