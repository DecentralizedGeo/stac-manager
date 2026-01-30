import json
import logging
from pathlib import Path
import pytest
from stac_manager.core.manager import StacManager
from stac_manager.utils.logging import setup_logger

@pytest.mark.asyncio
async def test_e2e_logging_workflow(tmp_path):
    """
    End-to-End test for verification of logging configuration and propagation.
    
    Creates inputs, workflow config, runs the manager, and verifies 
    that DEBUG logs are present in the output log file.
    """
    # 1. Setup Data Paths
    data_dir = tmp_path / "data"
    input_dir = tmp_path / "input-data"
    output_dir = tmp_path / "output"
    
    data_dir.mkdir()
    input_dir.mkdir()
    output_dir.mkdir()
    
    items_path = data_dir / "items.json"
    cloud_cover_path = input_dir / "cloud-cover.json"
    log_file = output_dir / "workflow.log"
    
    # 2. Create Test Data
    items = [
        {
            "type": "Feature",
            "stac_version": "1.0.0",
            "id": "item_1",
            "properties": {"datetime": "2026-01-29T00:00:00Z"},
            "collection": "test-collection",
            "assets": {}
        },
        {
            "type": "Feature",
            "stac_version": "1.0.0",
            "id": "item_2",
            "properties": {"datetime": "2026-01-29T00:00:00Z"},
            "collection": "test-collection",
            "assets": {}
        }
    ]
    with open(items_path, "w") as f:
        json.dump(items, f)
        
    cloud_cover_data = {
        "item_1": {"cloud_cover": 10},
        "item_2": {"cloud_cover": 20}
    }
    with open(cloud_cover_path, "w") as f:
        json.dump(cloud_cover_data, f)
        
    # 3. Create Workflow Config
    workflow_config = {
        "name": "e2e-logging-test",
        "settings": {
            "logging": {
                "level": "INFO",  # Global level
                "output_format": "text",
                "file": str(log_file),
                "progress_interval": 1
            }
        },
        "steps": [
            {
                "id": "ingest",
                "module": "IngestModule",
                "config": {
                    "mode": "file",
                    "source": str(items_path),
                    "source_type": "file",
                    "format": "json"
                },
                "log_level": "DEBUG"  # Override
            },
            {
                "id": "transform",
                "module": "TransformModule",
                "depends_on": ["ingest"],
                "config": {
                    "input_file": str(cloud_cover_path),
                    "field_mapping": {
                        "properties.cloud_cover": "cloud_cover"
                    },
                    "strategy": "update_existing"
                },
                "log_level": "DEBUG" # Override
            },
            {
                "id": "update",
                "module": "UpdateModule",
                "depends_on": ["transform"],
                "config": {
                    "updates": {
                        "properties.test_update": "updated"
                    },
                    "auto_update_timestamp": True
                },
                "log_level": "DEBUG" # Override
            },
            {
                "id": "output",
                "module": "OutputModule",
                "depends_on": ["update"],
                "config": {
                    "format": "json",
                    "base_dir": str(output_dir),
                    "buffer_size": 1
                }
            }
        ]
    }
    
    # 4. Run Workflow
    # Initialize logging (usually handled by CLI)
    setup_logger(workflow_config)
    
    manager = StacManager(config=workflow_config)
    result = await manager.execute()
    
    # 5. Assertions
    assert result.success
    assert result.total_items_processed == 2
    assert result.failure_count == 0
    
    # Verify Log File Content
    assert log_file.exists()
    log_content = log_file.read_text(encoding="utf-8")
    
    # Check for presence of DEBUG logs from various modules
    # Ingest DEBUG
    assert "Fetched item item_1" in log_content
    
    # Transform DEBUG
    assert "Matched input data | item: item_1" in log_content
    # Transform INFO (sanity check)
    assert "Enriched item | item: item_1" in log_content
    
    # Update DEBUG
    assert "Set field | item: item_1 | path: ('properties', 'test_update')" in log_content
    assert "Updated timestamp | item: item_1" in log_content
    
    # Global INFO should be present
    assert "Workflow 'e2e-logging-test' completed" in log_content
