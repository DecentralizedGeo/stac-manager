import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from stac_manager.modules.discovery import DiscoveryModule
from stac_manager.context import WorkflowContext

@pytest.mark.asyncio
async def test_discovery_fetch():
    config = {
        "catalog_url": "https://example.com/stac",
        "collection_ids": ["coll1"]
    }
    module = DiscoveryModule(config)
    
    # Mock client
    with patch('stac_manager.modules.discovery.Client') as MockClient:
        mock_client_instance = MockClient.open.return_value
        mock_coll = MagicMock()
        mock_coll.id = "coll1"
        mock_coll.to_dict.return_value = {"id": "coll1"}
        mock_client_instance.get_collections.return_value = [mock_coll]
        
        ctx = MagicMock(spec=WorkflowContext)
        ctx.data = {}
        
        items = []
        async for item in module.fetch(ctx):
            items.append(item)
            
        assert len(items) == 1
        assert items[0]['id'] == "coll1"
        assert ctx.data['catalog_url'] == "https://example.com/stac"
