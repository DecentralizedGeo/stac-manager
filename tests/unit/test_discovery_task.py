import pytest
from unittest.mock import MagicMock, patch
from stac_manager.modules.discovery import DiscoveryModule
from stac_manager.context import WorkflowContext

@pytest.mark.asyncio
async def test_discovery_yields_collections():
    config = {
        "catalog_url": "https://example.com/stac",
        "collection_ids": ["coll_1", "coll_2"]
    }
    
    # Mock WorkflowContext
    context = MagicMock(spec=WorkflowContext)
    context.data = {}
    context.logger = MagicMock()

    # Mock pystac_client
    with patch("stac_manager.modules.discovery.Client") as MockClient:
        client_instance = MockClient.open.return_value
        # verify get_collection is called
        # mock returned collection objects
        mock_c1 = MagicMock()
        mock_c1.id = "coll_1"
        mock_c2 = MagicMock()
        mock_c2.id = "coll_2"
        # The revised logic calls get_collection for each ID in the config
        client_instance.get_collection.side_effect = [mock_c1, mock_c2]
        
        module = DiscoveryModule(config)
        
        results = await module.fetch(context)
        
        assert len(results) == 2
        task1 = results[0]
        assert task1["type"] == "collection"
        assert task1["collection_id"] == "coll_1"
        assert task1["collection_obj"] == mock_c1
        # Check global context side effect
        assert context.data['catalog_url'] == "https://example.com/stac"
