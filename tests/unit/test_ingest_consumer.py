import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from stac_manager.modules.ingest import IngestModule
from stac_manager.context import WorkflowContext

@pytest.mark.asyncio
async def test_ingest_consumes_collections():
    # Mock Input Stream (Async Iterator of Collections)
    async def task_stream():
        yield {
            "type": "collection",
            "collection_id": "coll_1",
            "collection_obj": MagicMock() # Mock pystac collection
        }
    
    config = {"limit": 10} 
    module = IngestModule(config)
    context = MagicMock(spec=WorkflowContext)
    context.logger = MagicMock()
    # Mock catalog_url for client open
    context.data = {"catalog_url": "https://mock.com"}
    
    # We need to mock Client.open inside IngestModule to avoid real requests
    with patch("stac_manager.modules.ingest.Client") as MockClient:
        client_inst = MockClient.open.return_value
        # Mock search method
        mock_search = client_inst.search.return_value
        # items_as_dicts returns iterator
        mock_search.items_as_dicts.return_value = iter([{"id": "item1"}, {"id": "item2"}])
        
        # Execute fetch with items
        results = [i async for i in module.fetch(context, items=task_stream())]
        
        assert len(results) == 2
        assert results[0]["id"] == "item1"
        assert results[1]["id"] == "item2"
        # Verify search called with collection
        client_inst.search.assert_called()
