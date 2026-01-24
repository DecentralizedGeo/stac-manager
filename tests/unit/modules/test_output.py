"""Unit tests for OutputModule."""
import pytest
import json
import os
import pyarrow.parquet as pq
from pathlib import Path
from unittest.mock import patch
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


@pytest.mark.asyncio
async def test_output_atomic_write(tmp_path):
    """OutputModule uses atomic writes (temp file + rename)."""
    config = {
        "format": "json",
        "base_dir": str(tmp_path)
    }
    
    module = OutputModule(config)
    context = MockWorkflowContext.create()
    
    item = VALID_ITEM.copy()
    
    # Track file operations
    write_calls = []
    rename_calls = []
    
    original_write = Path.write_text
    original_replace = os.replace
    
    def track_write(self, content, *args, **kwargs):
        write_calls.append(str(self))
        return original_write(self, content, *args, **kwargs)
    
    def track_replace(src, dst):
        rename_calls.append((src, dst))
        return original_replace(src, dst)
    
    with patch.object(Path, 'write_text', track_write):
        with patch('os.replace', track_replace):
            await module.bundle(item, context)
            await module.finalize(context)
    
    # Verify atomic pattern: write to .tmp then rename
    assert len(write_calls) == 1
    assert write_calls[0].endswith('.tmp')
    
    assert len(rename_calls) == 1
    src, dst = rename_calls[0]
    assert src.endswith('.tmp')
    assert dst.endswith('.json')
    assert not dst.endswith('.tmp.json')


@pytest.mark.asyncio
async def test_output_buffering(tmp_path):
    """OutputModule buffers items and flushes at threshold."""
    config = {
        "format": "json",
        "base_dir": str(tmp_path),
        "buffer_size": 3  # Small buffer for testing
    }
    
    module = OutputModule(config)
    context = MockWorkflowContext.create()
    
    # Add 2 items - should not write yet
    await module.bundle({**VALID_ITEM, "id": "item-1"}, context)
    await module.bundle({**VALID_ITEM, "id": "item-2"}, context)
    
    assert len(list(tmp_path.glob("*.json"))) == 0
    
    # Add 3rd item - should trigger flush
    await module.bundle({**VALID_ITEM, "id": "item-3"}, context)
    
    assert len(list(tmp_path.glob("*.json"))) == 3
    
    # Add 2 more items - should not write yet
    await module.bundle({**VALID_ITEM, "id": "item-4"}, context)
    await module.bundle({**VALID_ITEM, "id": "item-5"}, context)
    
    assert len(list(tmp_path.glob("*.json"))) == 3
    
    # Finalize - should flush remaining
    await module.finalize(context)
    
    assert len(list(tmp_path.glob("*.json"))) == 5


@pytest.mark.asyncio
async def test_output_parquet(tmp_path):
    """OutputModule writes items as Parquet file."""
    config = {
        "format": "parquet",
        "base_dir": str(tmp_path),
        "buffer_size": 10
    }
    
    module = OutputModule(config)
    context = MockWorkflowContext.create()
    
    # Bundle multiple items with non-empty assets (PyArrow requirement)
    items = [
        {
            **VALID_ITEM, 
            "id": f"item-{i}",
            "assets": {"thumbnail": {"href": f"item-{i}.jpg"}}
        }
        for i in range(5)
    ]
    
    for item in items:
        await module.bundle(item, context)
    
    # Finalize
    result = await module.finalize(context)
    
    # Verify Parquet file exists
    parquet_files = list(tmp_path.glob("*.parquet"))
    assert len(parquet_files) == 1
    
    # Verify content
    table = pq.read_table(str(parquet_files[0]))
    assert len(table) == 5
    
    # Verify result
    assert result["items_written"] == 5
