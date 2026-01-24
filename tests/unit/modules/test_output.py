"""Unit tests for OutputModule."""
import pytest
import json
from pathlib import Path
from tests.fixtures.context import MockWorkflowContext
from tests.fixtures.stac_items import VALID_ITEM
from stac_manager.modules.output import OutputModule


@pytest.mark.asyncio
async def test_output_json_basic(tmp_path):
    """OutputModule writes items as JSON files."""
    config = {
        "format": "json",
        "base_dir": str(tmp_path)
    }
    
    module = OutputModule(config)
    context = MockWorkflowContext.create()
    
    # Bundle item
    item = VALID_ITEM.copy()
    await module.bundle(item, context)
    
    # Finalize
    result = await module.finalize(context)
    
    # Verify file exists
    item_file = tmp_path / f"{item['id']}.json"
    assert item_file.exists()
    
    # Verify content
    content = json.loads(item_file.read_text())
    assert content["id"] == item["id"]
    assert content["type"] == "Feature"
    
    # Verify result manifest
    assert result["items_written"] == 1


@pytest.mark.asyncio
async def test_output_creates_directory(tmp_path):
    """OutputModule creates output directory if missing."""
    output_dir = tmp_path / "nested" / "output"
    
    config = {
        "format": "json",
        "base_dir": str(output_dir)
    }
    
    module = OutputModule(config)
    context = MockWorkflowContext.create()
    
    await module.bundle(VALID_ITEM.copy(), context)
    await module.finalize(context)
    
    assert output_dir.exists()
