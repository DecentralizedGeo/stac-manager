import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from stac_manager.modules.ingest import IngestModule
from stac_manager.context import WorkflowContext

@pytest.mark.asyncio
async def test_ingest_fetch():
    config = {
        "collection_id": "coll1",
        "limit": 10
    }
    module = IngestModule(config)
    
    ctx = MagicMock(spec=WorkflowContext)
    ctx.data = {"catalog_url": "https://example.com"}
    
    with patch('stac_manager.modules.ingest.Client') as MockClient:
        mock_client_instance = MockClient.open.return_value
        mock_search = mock_client_instance.search.return_value
        
        mock_item = MagicMock()
        mock_item.id = "item1" # Fix for attribute access
        mock_item.to_dict.return_value = {"id": "item1"}
        mock_search.items.return_value = [mock_item]
        
        items = []
        async for item in module.fetch(ctx):
            items.append(item)
            
        assert len(items) == 1
        assert items[0]['id'] == "item1"
        
        # Verify search called with limits
        mock_client_instance.search.assert_called_with(
            collections=["coll1"],
            max_items=10
        )
