"""Tests for sample data generator script."""
import csv
import json
import tempfile
from unittest.mock import Mock, patch
from pathlib import Path

from click.testing import CliRunner
from pystac import Item

from scripts.generate_sample_data import cli


def test_cli_help():
    """Test CLI help flag displays usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    
    assert result.exit_code == 0
    assert 'generate-sample-data' in result.output.lower()
    assert '--collection' in result.output
    assert '--items' in result.output


def test_cli_requires_collection():
    """Test CLI fails without collection argument."""
    runner = CliRunner()
    result = runner.invoke(cli, [])
    
    assert result.exit_code != 0


def test_fetch_sentinel2_items_returns_20_items():
    """Test fetching returns correct number of items."""
    from scripts.generate_sample_data import fetch_stac_items
    
    # Mock pystac-client response
    mock_items = [
        Mock(spec=Item, id=f"S2A_ITEM_{i}", to_dict=lambda: {"id": f"S2A_ITEM_{i}"})
        for i in range(20)
    ]
    
    with patch('scripts.generate_sample_data.Client') as mock_client:
        mock_search = Mock()
        mock_search.items.return_value = iter(mock_items)
        mock_client.open.return_value.search.return_value = mock_search
        
        items = fetch_stac_items(
            catalog_url="https://planetarycomputer.microsoft.com/api/stac/v1",
            collection_id="sentinel-2-l2a",
            max_items=20
        )
        
        assert len(items) == 20
        assert all(isinstance(item, dict) for item in items)


def test_fetch_applies_bbox_filter():
    """Test that bbox filter is applied to search."""
    from scripts.generate_sample_data import fetch_stac_items
    
    with patch('scripts.generate_sample_data.Client') as mock_client:
        mock_search = Mock()
        mock_search.items.return_value = iter([])
        mock_client.open.return_value.search.return_value = mock_search
        
        fetch_stac_items(
            catalog_url="https://test.com",
            collection_id="test",
            max_items=5,
            bbox=[-122.5, 37.5, -122.0, 38.0]
        )
        
        # Verify search was called with bbox
        call_kwargs = mock_client.open.return_value.search.call_args[1]
        assert 'bbox' in call_kwargs
        assert call_kwargs['bbox'] == [-122.5, 37.5, -122.0, 38.0]


def test_save_items_as_json(tmp_path):
    """Test saving items to JSON file."""
    from scripts.generate_sample_data import save_items_as_json
    
    items = [
        {"id": "item1", "type": "Feature", "properties": {}},
        {"id": "item2", "type": "Feature", "properties": {}}
    ]
    
    output_path = tmp_path / "items.json"
    save_items_as_json(items, output_path)
    
    assert output_path.exists()
    
    with open(output_path) as f:
        loaded = json.load(f)
    
    assert len(loaded) == 2
    assert loaded[0]["id"] == "item1"


def test_convert_to_parquet(tmp_path):
    """Test converting JSON items to Parquet."""
    from scripts.generate_sample_data import convert_to_parquet
    
    # Create JSON file with complete STAC items
    items = [
        {
            "id": "item1",
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
            "properties": {"datetime": "2023-01-01T00:00:00Z"},
            "links": [],
            "assets": {"data": {"href": "s3://bucket/data1.tif"}},
            "bbox": [0, 0, 0, 0],
            "stac_version": "1.0.0"
        },
        {
            "id": "item2",
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [1, 1]},
            "properties": {"datetime": "2023-01-02T00:00:00Z"},
            "links": [],
            "assets": {"data": {"href": "s3://bucket/data2.tif"}},
            "bbox": [1, 1, 1, 1],
            "stac_version": "1.0.0"
        }
    ]
    json_path = tmp_path / "items.json"
    with open(json_path, 'w') as f:
        json.dump(items, f)
    
    parquet_path = tmp_path / "items.parquet"
    convert_to_parquet(json_path, parquet_path)
    
    assert parquet_path.exists()
    
    # Verify round-trip
    import pyarrow.parquet as pq
    table = pq.read_table(parquet_path)
    assert len(table) == 2


def test_extract_collection_metadata():
    """Test extracting collection metadata from API."""
    from scripts.generate_sample_data import extract_collection_metadata
    
    with patch('scripts.generate_sample_data.Client') as mock_client:
        mock_collection = Mock()
        mock_collection.to_dict.return_value = {
            "id": "sentinel-2-l2a",
            "description": "Test collection",
            "extent": {},
            "license": "proprietary",
            "links": [],
            "unnecessary_field": "remove_this"
        }
        mock_client.open.return_value.get_collection.return_value = mock_collection
        
        metadata = extract_collection_metadata(
            catalog_url="https://test.com",
            collection_id="sentinel-2-l2a"
        )
        
        assert metadata["id"] == "sentinel-2-l2a"
        assert "description" in metadata
        assert "unnecessary_field" not in metadata
