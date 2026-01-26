"""End-to-end orchestration tests."""
import asyncio
import json
from pathlib import Path
import tempfile
from stac_manager import StacManager


def test_complete_workflow_execution():
    """Test complete workflow: ingest → transform → validate → output."""
    
    async def run_test(tmp_path):
        # Create test data
        test_items_path = tmp_path / "test_items.json"
        test_items = [
            {
                "type": "Feature",
                "stac_version": "1.0.0",
                "id": f"test-item-{i}",
                "geometry": {"type": "Point", "coordinates": [float(i), float(i)]},
                "bbox": [float(i), float(i), float(i), float(i)],
                "properties": {
                    "datetime": "2024-01-01T00:00:00Z",
                    "test_value": i
                },
                "links": [],
                "assets": {}
            }
            for i in range(10)
        ]
        
        with open(test_items_path, 'w') as f:
            json.dump(test_items, f)
        
        # Create workflow
        config = {
            "name": "complete-e2e-workflow",
            "steps": [
                {
                    "id": "ingest",
                    "module": "IngestModule",
                    "config": {
                        "mode": "file",
                        "source": str(test_items_path),
                        "format": "json"
                    }
                },
                {
                    "id": "update",
                    "module": "UpdateModule",
                    "config": {
                        "fields": {"properties.processed": True}
                    },
                    "depends_on": ["ingest"]
                },
                {
                    "id": "validate",
                    "module": "ValidateModule",
                    "config": {},
                    "depends_on": ["update"]
                },
                {
                    "id": "output",
                    "module": "OutputModule",
                    "config": {
                        "base_dir": str(tmp_path / "output"),
                        "format": "json"
                    },
                    "depends_on": ["validate"]
                }
            ]
        }
        
        # Execute
        manager = StacManager(config=config, checkpoint_dir=tmp_path / "checkpoints")
        result = await manager.execute()
        
        # Verify success
        assert result.success
        assert result.total_items_processed == 10
        assert result.failure_count == 0
        
        # Verify output exists
        output_dir = tmp_path / "output"
        assert output_dir.exists()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        asyncio.run(run_test(Path(tmpdir)))


def test_workflow_with_failures_continues():
    """Test workflow continues despite item-level failures."""
    
    async def run_test(tmp_path):
        # Create test data with items that will cause validation failures
        test_items_path = tmp_path / "test_items.json"
        test_items = []
        
        for i in range(10):
            item = {
                "type": "Feature",
                "stac_version": "1.0.0",
                "id": f"item-{i}",
                "geometry": {"type": "Point", "coordinates": [0, 0]},
                "bbox": [0, 0, 0, 0],
                "properties": {"datetime": "2024-01-01T00:00:00Z"},
                "links": [],
                "assets": {}
            }
            
            # Every third item is missing required fields (will fail validation)
            if i % 3 == 0:
                del item["properties"]["datetime"]
            
            test_items.append(item)
        
        with open(test_items_path, 'w') as f:
            json.dump(test_items, f)
        
        config = {
            "name": "failure-tolerance-workflow",
            "steps": [
                {
                    "id": "ingest",
                    "module": "IngestModule",
                    "config": {
                        "mode": "file",
                        "source": str(test_items_path),
                        "format": "json"
                    }
                },
                {
                    "id": "validate",
                    "module": "ValidateModule",
                    "config": {"strict": True},
                    "depends_on": ["ingest"]
                },
                {
                    "id": "output",
                    "module": "OutputModule",
                    "config": {
                        "base_dir": str(tmp_path / "output"),
                        "format": "json"
                    },
                    "depends_on": ["validate"]
                }
            ]
        }
        
        manager = StacManager(config=config, checkpoint_dir=tmp_path / "checkpoints")
        result = await manager.execute()
        
        # Should complete with failures
        assert result.status == 'completed_with_failures'
        assert result.failure_count > 0
        # Items that fail validation may not be counted in total_items_processed
        assert result.total_items_processed + result.failure_count == 10
    
    with tempfile.TemporaryDirectory() as tmpdir:
        asyncio.run(run_test(Path(tmpdir)))


def test_workflow_with_multiple_modifiers():
    """Test workflow with multiple sequential modifiers."""
    
    async def run_test(tmp_path):
        test_items_path = tmp_path / "test_items.json"
        test_items = [
            {
                "type": "Feature",
                "stac_version": "1.0.0",
                "id": "test-item",
                "geometry": {"type": "Point", "coordinates": [0, 0]},
                "bbox": [0, 0, 0, 0],
                "properties": {"datetime": "2024-01-01T00:00:00Z"},
                "links": [],
                "assets": {}
            }
        ]
        
        with open(test_items_path, 'w') as f:
            json.dump(test_items, f)
        
        config = {
            "name": "multi-modifier-workflow",
            "steps": [
                {
                    "id": "ingest",
                    "module": "IngestModule",
                    "config": {
                        "mode": "file",
                        "source": str(test_items_path),
                        "format": "json"
                    }
                },
                {
                    "id": "update1",
                    "module": "UpdateModule",
                    "config": {"fields": {"properties.step1": "done"}},
                    "depends_on": ["ingest"]
                },
                {
                    "id": "update2",
                    "module": "UpdateModule",
                    "config": {"fields": {"properties.step2": "done"}},
                    "depends_on": ["update1"]
                },
                {
                    "id": "update3",
                    "module": "UpdateModule",
                    "config": {"fields": {"properties.step3": "done"}},
                    "depends_on": ["update2"]
                },
                {
                    "id": "output",
                    "module": "OutputModule",
                    "config": {
                        "base_dir": str(tmp_path / "output"),
                        "format": "json"
                    },
                    "depends_on": ["update3"]
                }
            ]
        }
        
        manager = StacManager(config=config, checkpoint_dir=tmp_path / "checkpoints")
        result = await manager.execute()
        
        assert result.success
        assert result.total_items_processed == 1
    
    with tempfile.TemporaryDirectory() as tmpdir:
        asyncio.run(run_test(Path(tmpdir)))
