"""Tests for sample data generator script."""
from unittest.mock import Mock, patch
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
