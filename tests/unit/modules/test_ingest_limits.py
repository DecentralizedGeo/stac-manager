
import pytest
import json
import logging
from unittest.mock import MagicMock, AsyncMock
from stac_manager.modules.ingest import IngestModule
from stac_manager.core.context import WorkflowContext

@pytest.fixture
def mock_context():
    ctx = MagicMock(spec=WorkflowContext)
    ctx.logger = logging.getLogger("test")
    return ctx

@pytest.fixture
def items_file(tmp_path):
    items = [{"type": "Feature", "id": f"item-{i}", "properties": {}} for i in range(10)]
    file_path = tmp_path / "items.json"
    file_path.write_text(json.dumps(items))
    return str(file_path)

@pytest.mark.asyncio
async def test_file_ingest_max_items_limit(items_file, mock_context):
    """Test that max_items limits the number of items yielded from a file."""
    config = {
        "mode": "file",
        "source": items_file,
        "max_items": 5
    }
    ingest = IngestModule(config)
    
    items = []
    async for item in ingest.fetch(mock_context):
        items.append(item)
        
    assert len(items) == 5
    assert items[0]["id"] == "item-0"
    assert items[4]["id"] == "item-4"

@pytest.mark.asyncio
async def test_file_ingest_limit_ignored(items_file, mock_context):
    """Test that the 'limit' parameter is ignored in file mode (it's for API only)."""
    config = {
        "mode": "file",
        "source": items_file,
        "limit": 5  # Should be ignored
    }
    ingest = IngestModule(config)
    
    items = []
    async for item in ingest.fetch(mock_context):
        items.append(item)
        
    assert len(items) == 10  # All 10 items should be returned

@pytest.mark.asyncio
async def test_file_ingest_no_limit(items_file, mock_context):
    """Test that no limit returns all items."""
    config = {
        "mode": "file",
        "source": items_file
    }
    ingest = IngestModule(config)
    
    items = []
    async for item in ingest.fetch(mock_context):
        items.append(item)
        
    assert len(items) == 10
