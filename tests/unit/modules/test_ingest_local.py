import pytest
import json
import os
from stac_manager.modules.ingest import IngestModule

@pytest.mark.asyncio
async def test_ingest_from_json_file(tmp_path):
    # Create a dummy source file
    source_file = tmp_path / "items.json"
    items = [{"id": "item1", "type": "Feature", "properties": {}}]
    with open(source_file, "w") as f:
        json.dump(items, f)
        
    config = {
        "collection_id": "test-coll",
        "source_file": str(source_file)
    }
    
    module = IngestModule(config)
    results = []
    # Mock context not needed for file fetch usually, or minimal
    # We pass None as items because this module acts as a 'generator' when source_file is present
    # But usually Ingest is a 'consumer' of items.
    # The plan says: "Enhanced with source_file support... using a simple strategy pattern within fetch"
    # If source_file is set, it yields items from file, ignoring input stream?
    # Let's check plan implementation detail:
    # "if self.config.source_file: for item in self.fetch_from_file... yield item; return"
    # So yes, it acts as a generator.
    
    # We need to simulate the pipeline calling fetch with a context.
    # We can pass a dummy context or None if not used. 
    # But IngestModule.fetch expects context.logger to exist.
    
    from unittest.mock import MagicMock
    mock_context = MagicMock()
    
    async for item in module.fetch(mock_context, items=[]):
        results.append(item)
        
    assert len(results) == 1
    assert results[0]["id"] == "item1"
