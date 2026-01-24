"""Tests for IngestModule."""
import pytest
import json
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
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


@pytest.mark.asyncio
async def test_ingest_parquet_file_success(tmp_path):
    """IngestModule reads items from Parquet file."""
    # Create test Parquet file
    parquet_file = tmp_path / "items.parquet"
    # Use items with non-empty assets to avoid Parquet struct issue
    test_items = [
        {**VALID_ITEM, "assets": {"data": {"href": "test.tif"}}},
        {**VALID_ITEM, "id": "test-item-002", "assets": {"data": {"href": "test2.tif"}}}
    ]
    
    # Convert to Arrow Table
    table = pa.Table.from_pylist(test_items)
    pq.write_table(table, parquet_file)
    
    # Configure module
    config = {
        "mode": "file",
        "source": str(parquet_file),
        "format": "parquet"
    }
    module = IngestModule(config)
    context = MockWorkflowContext.create()
    
    # Fetch items
    results = [item async for item in module.fetch(context)]
    
    assert len(results) == 2
    assert results[0]["id"] == "test-item-001"


@pytest.mark.asyncio
async def test_ingest_api_search_success():
    """IngestModule fetches items from STAC API."""
    # Mock API client and search results
    mock_client = MagicMock()
    mock_search = MagicMock()
    
    # Mock items_as_dicts to return regular iterator (not async)
    test_items = [VALID_ITEM.copy(), {**VALID_ITEM, "id": "test-item-002"}]
    mock_search.items_as_dicts.return_value = iter(test_items)
    mock_client.search.return_value = mock_search
    
    # Configure module for API mode
    config = {
        "mode": "api",
        "source": "https://example.com/stac",
        "collections": ["sentinel-2"],
        "limit": 100
    }
    
    with patch('pystac_client.Client.open', return_value=mock_client):
        module = IngestModule(config)
        context = MockWorkflowContext.create()
        
        # Fetch items
        results = [item async for item in module.fetch(context)]
    
    assert len(results) == 2
    assert results[0]["id"] == "test-item-001"
    assert results[1]["id"] == "test-item-002"
    
    # Verify search was called with correct params
    mock_client.search.assert_called_once()
    call_kwargs = mock_client.search.call_args.kwargs
    assert call_kwargs["collections"] == ["sentinel-2"]
    assert call_kwargs["limit"] == 100
