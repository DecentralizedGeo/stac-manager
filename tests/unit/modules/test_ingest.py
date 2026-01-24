"""Tests for IngestModule."""
import pytest
import json
from pathlib import Path
from tests.fixtures.context import MockWorkflowContext
from tests.fixtures.stac_items import VALID_ITEM
from stac_manager.modules.ingest import IngestModule


@pytest.mark.asyncio
async def test_ingest_json_file_success(tmp_path):
    """IngestModule reads items from JSON file."""
    # Create test JSON file with item list
    items_file = tmp_path / "items.json"
    test_items = [VALID_ITEM.copy(), {**VALID_ITEM, "id": "test-item-002"}]
    items_file.write_text(json.dumps(test_items))
    
    # Configure module for file mode
    config = {
        "mode": "file",
        "source": str(items_file),
        "format": "json"
    }
    module = IngestModule(config)
    context = MockWorkflowContext.create()
    
    # Fetch items
    results = [item async for item in module.fetch(context)]
    
    assert len(results) == 2
    assert results[0]["id"] == "test-item-001"
    assert results[1]["id"] == "test-item-002"


@pytest.mark.asyncio
async def test_ingest_json_file_not_found():
    """IngestModule raises ConfigurationError for missing file."""
    config = {
        "mode": "file",
        "source": "/nonexistent/items.json",
        "format": "json"
    }
    
    from stac_manager.exceptions import ConfigurationError
    with pytest.raises(ConfigurationError, match="File not found"):
        module = IngestModule(config)
