import pytest
import shutil
import json
import os
from unittest.mock import patch, MagicMock
from stac_manager.manager import StacManager
from stac_manager.config import WorkflowDefinition

@pytest.mark.asyncio
async def test_full_pipeline_integration(tmp_path):
    # 1. Define Workflow
    # Discovery -> Transform -> Output
    target_output = tmp_path / "output"
    workflow_dict = {
        "name": "integration-test",
        "steps": [
            {
                "id": "discover", 
                "module": "DiscoveryModule",
                "config": {"catalog_url": "https://mock.test/stac"}
            },
            {
                "id": "transform",
                "module": "TransformModule",
                "depends_on": ["discover"],
                "config": {
                    "mappings": [
                        {"source_field": "id", "target_field": "id", "type": "string"},
                        {"source_field": "id", "target_field": "properties.original_id", "type": "string"}
                    ]
                }
            },
            {
                "id": "output",
                "module": "OutputModule",
                "depends_on": ["transform"],
                "config": {
                    "format": "json",
                    "output_path": str(target_output),
                    "organize_by": "flat"
                }
            }
        ]
    }
    wf_def = WorkflowDefinition(**workflow_dict)
    
    # 2. Mock External API (DiscoveryModule fetch)
    # We patch the DiscoveryModule.fetch to yield dicts directly, bypassing pystac_client
    # OR better, patch pystac_client.Client.open to return a mock client
    with patch("stac_manager.modules.discovery.Client") as MockClient:
        mock_client = MockClient.open.return_value
        # mock collections
        c1 = MagicMock()
        c1.to_dict.return_value = {"id": "coll1", "type": "Collection"}
        
        # DiscoveryModule iterates collections.
        # Wait, usually Discovery passes catalog_url to Ingest. 
        # But here we are piping Discovery output (Collections) -> Transform -> Output.
        # This is valid: transforming collection metadata.
        
        mock_client.get_collections.return_value = [c1]
        
        # 3. Execute
        manager = StacManager(wf_def)
        result = await manager.execute()
        
        # 4. Verify
        assert result['success'] is True
        assert result['failure_count'] == 0
        
        # Verify Output
        expected_file = target_output / "coll1.json"
        assert expected_file.exists()
        
        with open(expected_file) as f:
            data = json.load(f)
            assert data['id'] == "coll1"
            assert data['properties']['original_id'] == "coll1"
