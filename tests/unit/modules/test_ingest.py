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
        "collection_id": "sentinel-2",
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
    assert call_kwargs["collections"] == ["sentinel-2"]  # Passed as list internally
    assert call_kwargs["limit"] == 100


@pytest.mark.asyncio
async def test_ingest_api_collection_from_context():
    """IngestModule uses collection_id from context when not in config (Matrix Strategy)."""
    # Mock API client and search results
    mock_client = MagicMock()
    mock_search = MagicMock()
    
    test_items = [VALID_ITEM.copy()]
    mock_search.items_as_dicts.return_value = iter(test_items)
    mock_client.search.return_value = mock_search
    
    # Configure module WITHOUT collection_id
    config = {
        "mode": "api",
        "source": "https://example.com/stac",
        "limit": 100
    }
    
    with patch('pystac_client.Client.open', return_value=mock_client):
        module = IngestModule(config)
        # Inject collection_id via context (as Matrix Strategy would)
        context = MockWorkflowContext.create(data={'collection_id': 'landsat-8'})
        
        # Fetch items
        results = [item async for item in module.fetch(context)]
    
    assert len(results) == 1
    
    # Verify collection_id was picked up from context
    call_kwargs = mock_client.search.call_args.kwargs
    assert call_kwargs["collections"] == ["landsat-8"]


@pytest.mark.asyncio
async def test_ingest_api_missing_collection_id():
    """IngestModule raises error when collection_id not in config or context."""
    mock_client = MagicMock()
    
    config = {
        "mode": "api",
        "source": "https://example.com/stac",
    }
    
    from stac_manager.exceptions import ConfigurationError
    with patch('pystac_client.Client.open', return_value=mock_client):
        module = IngestModule(config)
        context = MockWorkflowContext.create()  # No collection_id in context
        
        with pytest.raises(ConfigurationError, match="collection_id must be provided"):
            _ = [item async for item in module.fetch(context)]


@pytest.mark.asyncio
async def test_ingest_api_filters_bbox():
    """IngestModule passes bbox filter to API search."""
    mock_client = MagicMock()
    mock_search = MagicMock()
    
    test_items = [VALID_ITEM.copy()]
    mock_search.items_as_dicts.return_value = iter(test_items)
    mock_client.search.return_value = mock_search
    
    config = {
        "mode": "api",
        "source": "https://example.com/stac",
        "collection_id": "test-collection",
        "bbox": [-180, -90, 180, 90]
    }
    
    with patch('pystac_client.Client.open', return_value=mock_client):
        module = IngestModule(config)
        context = MockWorkflowContext.create()
        _ = [item async for item in module.fetch(context)]
    
    call_kwargs = mock_client.search.call_args.kwargs
    assert call_kwargs["bbox"] == [-180, -90, 180, 90]


@pytest.mark.asyncio
async def test_ingest_api_filters_datetime():
    """IngestModule passes datetime filter to API search."""
    mock_client = MagicMock()
    mock_search = MagicMock()
    
    test_items = [VALID_ITEM.copy()]
    mock_search.items_as_dicts.return_value = iter(test_items)
    mock_client.search.return_value = mock_search
    
    config = {
        "mode": "api",
        "source": "https://example.com/stac",
        "collection_id": "test-collection",
        "datetime": "2023-01-01/2023-12-31"
    }
    
    with patch('pystac_client.Client.open', return_value=mock_client):
        module = IngestModule(config)
        context = MockWorkflowContext.create()
        _ = [item async for item in module.fetch(context)]
    
    call_kwargs = mock_client.search.call_args.kwargs
    assert call_kwargs["datetime"] == "2023-01-01/2023-12-31"


@pytest.mark.asyncio
async def test_ingest_api_filters_query():
    """IngestModule passes CQL query filter to API search."""
    mock_client = MagicMock()
    mock_search = MagicMock()
    
    test_items = [VALID_ITEM.copy()]
    mock_search.items_as_dicts.return_value = iter(test_items)
    mock_client.search.return_value = mock_search
    
    query_filter = {"eo:cloud_cover": {"lt": 10}}
    config = {
        "mode": "api",
        "source": "https://example.com/stac",
        "collection_id": "test-collection",
        "query": query_filter
    }
    
    with patch('pystac_client.Client.open', return_value=mock_client):
        module = IngestModule(config)
        context = MockWorkflowContext.create()
        _ = [item async for item in module.fetch(context)]
    
    call_kwargs = mock_client.search.call_args.kwargs
    assert call_kwargs["query"] == query_filter


@pytest.mark.asyncio
async def test_ingest_api_connection_error():
    """IngestModule raises DataProcessingError on connection failures."""
    mock_client = MagicMock()
    mock_client.search.side_effect = ConnectionError("Network unreachable")
    
    config = {
        "mode": "api",
        "source": "https://example.com/stac",
        "collection_id": "test-collection"
    }
    
    from stac_manager.exceptions import DataProcessingError
    with patch('pystac_client.Client.open', return_value=mock_client):
        module = IngestModule(config)
        context = MockWorkflowContext.create()
        
        with pytest.raises(DataProcessingError, match="Network unreachable"):
            _ = [item async for item in module.fetch(context)]


@pytest.mark.asyncio
async def test_ingest_file_read_error():
    """IngestModule raises DataProcessingError on file read failures."""
    # Create a file and then make it unreadable
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([VALID_ITEM], f)
        temp_file = f.name
    
    try:
        config = {
            "mode": "file",
            "source": temp_file,
        }
        module = IngestModule(config)
        context = MockWorkflowContext.create()
        
        # Make file unreadable by deleting it
        os.remove(temp_file)
        
        # Now fetch should fail - could be ConfigurationError (path check) or DataProcessingError (read error)
        from stac_manager.exceptions import DataProcessingError, ConfigurationError
        with pytest.raises((DataProcessingError, ConfigurationError)):
            _ = [item async for item in module.fetch(context)]
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_ingest_protocol_compliance():
    """IngestModule implements Fetcher protocol."""
    from stac_manager.protocols import Fetcher
    import tempfile
    import os

    config = {
        "mode": "file",
        "source": "/tmp/items.json",
        "format": "json"
    }

    # Create temp file with valid item
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([VALID_ITEM.copy()], f)
        temp_file = f.name

    try:
        config["source"] = temp_file
        module = IngestModule(config)

        # Check protocol compliance
        assert isinstance(module, Fetcher), "IngestModule must implement Fetcher protocol"
        assert hasattr(module, 'fetch'), "IngestModule must have fetch method"
        assert callable(module.fetch), "fetch must be callable"
    finally:
        os.unlink(temp_file)


# =============================================================================
# Source Type Detection Tests
# =============================================================================

@pytest.mark.asyncio
async def test_ingest_items_directory_auto_detect(tmp_path):
    """IngestModule auto-detects items directory and loads all JSON files."""
    # Create items directory with multiple JSON files
    items_dir = tmp_path / "items"
    items_dir.mkdir()
    
    # Create 3 item files
    for i in range(3):
        item_file = items_dir / f"item_{i:03d}.json"
        item = {**VALID_ITEM, "id": f"test-item-{i:03d}"}
        item_file.write_text(json.dumps(item))
    
    config = {
        "mode": "file",
        "source": str(items_dir)
        # No source_type - should auto-detect
    }
    module = IngestModule(config)
    context = MockWorkflowContext.create()
    
    results = [item async for item in module.fetch(context)]
    
    assert len(results) == 3
    assert results[0]["id"] == "test-item-000"
    assert results[1]["id"] == "test-item-001"
    assert results[2]["id"] == "test-item-002"


@pytest.mark.asyncio
async def test_ingest_items_directory_explicit(tmp_path):
    """IngestModule loads items when source_type='items_directory' is explicit."""
    items_dir = tmp_path / "items"
    items_dir.mkdir()
    
    item_file = items_dir / "item.json"
    item_file.write_text(json.dumps(VALID_ITEM))
    
    config = {
        "mode": "file",
        "source": str(items_dir),
        "source_type": "items_directory"
    }
    module = IngestModule(config)
    context = MockWorkflowContext.create()
    
    results = [item async for item in module.fetch(context)]
    
    assert len(results) == 1
    assert results[0]["id"] == "test-item-001"


@pytest.mark.asyncio
async def test_ingest_collection_root_auto_detect(tmp_path):
    """IngestModule auto-detects collection root and loads items from items/ subdirectory."""
    # Create collection structure: collection.json + items/
    collection_dir = tmp_path / "my-collection"
    collection_dir.mkdir()
    
    # Create collection.json
    collection_file = collection_dir / "collection.json"
    collection_file.write_text(json.dumps({
        "type": "Collection",
        "id": "my-collection",
        "stac_version": "1.0.0"
    }))
    
    # Create items directory
    items_dir = collection_dir / "items"
    items_dir.mkdir()
    
    # Add items
    for i in range(2):
        item_file = items_dir / f"item_{i}.json"
        item = {**VALID_ITEM, "id": f"collection-item-{i}"}
        item_file.write_text(json.dumps(item))
    
    config = {
        "mode": "file",
        "source": str(collection_dir)
        # Should auto-detect collection root
    }
    module = IngestModule(config)
    context = MockWorkflowContext.create()
    
    results = [item async for item in module.fetch(context)]
    
    assert len(results) == 2
    assert results[0]["id"] == "collection-item-0"
    assert results[1]["id"] == "collection-item-1"


@pytest.mark.asyncio
async def test_ingest_collection_json_file_auto_detect(tmp_path):
    """IngestModule auto-detects collection.json file and loads from adjacent items/."""
    collection_dir = tmp_path / "my-collection"
    collection_dir.mkdir()
    
    collection_file = collection_dir / "collection.json"
    collection_file.write_text(json.dumps({
        "type": "Collection",
        "id": "my-collection"
    }))
    
    items_dir = collection_dir / "items"
    items_dir.mkdir()
    
    item_file = items_dir / "item.json"
    item_file.write_text(json.dumps(VALID_ITEM))
    
    # Point directly to collection.json file
    config = {
        "mode": "file",
        "source": str(collection_file)
    }
    module = IngestModule(config)
    context = MockWorkflowContext.create()
    
    results = [item async for item in module.fetch(context)]
    
    assert len(results) == 1
    assert results[0]["id"] == "test-item-001"


@pytest.mark.asyncio
async def test_ingest_collection_explicit_source_type(tmp_path):
    """IngestModule respects explicit source_type='collection'."""
    collection_dir = tmp_path / "my-collection"
    collection_dir.mkdir()
    
    collection_file = collection_dir / "collection.json"
    collection_file.write_text(json.dumps({"type": "Collection", "id": "test"}))
    
    items_dir = collection_dir / "items"
    items_dir.mkdir()
    
    item_file = items_dir / "item.json"
    item_file.write_text(json.dumps(VALID_ITEM))
    
    config = {
        "mode": "file",
        "source": str(collection_dir),
        "source_type": "collection"
    }
    module = IngestModule(config)
    context = MockWorkflowContext.create()
    
    results = [item async for item in module.fetch(context)]
    
    assert len(results) == 1


@pytest.mark.asyncio
async def test_ingest_format_auto_detection(tmp_path):
    """IngestModule auto-detects file format from extension."""
    # Test JSON auto-detection
    json_file = tmp_path / "items.json"
    json_file.write_text(json.dumps([VALID_ITEM]))
    
    config = {
        "mode": "file",
        "source": str(json_file)
        # No format specified - should auto-detect from .json extension
    }
    module = IngestModule(config)
    context = MockWorkflowContext.create()
    
    results = [item async for item in module.fetch(context)]
    assert len(results) == 1
    assert results[0]["id"] == "test-item-001"


@pytest.mark.asyncio
async def test_ingest_explicit_source_type_validation(tmp_path):
    """IngestModule validates explicit source_type matches path type."""
    # Create a directory
    items_dir = tmp_path / "items"
    items_dir.mkdir()
    
    # Try to use source_type='file' on a directory - should fail
    config = {
        "mode": "file",
        "source": str(items_dir),
        "source_type": "file"
    }
    
    from stac_manager.exceptions import ConfigurationError
    with pytest.raises(ConfigurationError, match="source_type='file' specified but .* is a directory"):
        module = IngestModule(config)
        context = MockWorkflowContext.create()
        _ = [item async for item in module.fetch(context)]


@pytest.mark.asyncio
async def test_ingest_items_directory_empty(tmp_path):
    """IngestModule raises error for empty items directory."""
    items_dir = tmp_path / "items"
    items_dir.mkdir()
    
    config = {
        "mode": "file",
        "source": str(items_dir)
    }
    module = IngestModule(config)
    context = MockWorkflowContext.create()
    
    from stac_manager.exceptions import DataProcessingError
    with pytest.raises(DataProcessingError, match="No JSON files found"):
        _ = [item async for item in module.fetch(context)]


@pytest.mark.asyncio
async def test_ingest_items_directory_skips_invalid_files(tmp_path):
    """IngestModule skips invalid JSON files and continues loading valid ones."""
    items_dir = tmp_path / "items"
    items_dir.mkdir()
    
    # Create valid item
    valid_file = items_dir / "valid.json"
    valid_file.write_text(json.dumps(VALID_ITEM))
    
    # Create invalid JSON file
    invalid_file = items_dir / "invalid.json"
    invalid_file.write_text("{invalid json")
    
    # Create another valid item
    valid_file2 = items_dir / "valid2.json"
    valid_file2.write_text(json.dumps({**VALID_ITEM, "id": "test-item-002"}))
    
    config = {
        "mode": "file",
        "source": str(items_dir)
    }
    module = IngestModule(config)
    context = MockWorkflowContext.create()
    
    results = [item async for item in module.fetch(context)]
    
    # Should load 2 valid items, skip 1 invalid
    assert len(results) == 2
    assert results[0]["id"] == "test-item-001"
    assert results[1]["id"] == "test-item-002"


@pytest.mark.asyncio
async def test_ingest_collection_with_inline_items(tmp_path):
    """IngestModule loads inline items from collection.json when no items/ directory exists."""
    collection_file = tmp_path / "collection.json"
    collection_data = {
        "type": "Collection",
        "id": "inline-collection",
        "features": [
            VALID_ITEM,
            {**VALID_ITEM, "id": "inline-item-002"}
        ]
    }
    collection_file.write_text(json.dumps(collection_data))
    
    config = {
        "mode": "file",
        "source": str(collection_file)
    }
    module = IngestModule(config)
    context = MockWorkflowContext.create()
    
    results = [item async for item in module.fetch(context)]
    
    assert len(results) == 2
    assert results[0]["id"] == "test-item-001"
    assert results[1]["id"] == "inline-item-002"


@pytest.mark.asyncio
async def test_ingest_collection_no_items_error(tmp_path):
    """IngestModule raises error when collection has no items/ and no inline features."""
    collection_dir = tmp_path / "my-collection"
    collection_dir.mkdir()
    
    collection_file = collection_dir / "collection.json"
    collection_file.write_text(json.dumps({
        "type": "Collection",
        "id": "empty-collection"
        # No features field
    }))
    
    config = {
        "mode": "file",
        "source": str(collection_file)
    }
    module = IngestModule(config)
    context = MockWorkflowContext.create()
    
    from stac_manager.exceptions import ConfigurationError
    with pytest.raises(ConfigurationError, match="No items/ directory found and no inline features"):
        _ = [item async for item in module.fetch(context)]
