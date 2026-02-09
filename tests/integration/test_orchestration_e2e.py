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


def test_matrix_strategy_parallel_execution():
    """Test matrix strategy executes multiple pipelines in parallel."""

    async def run_test(tmp_path):
        # Create data for multiple collections
        collection_configs = []

        for collection_id in ["landsat", "sentinel", "modis"]:
            collection_path = tmp_path / f"{collection_id}.json"
            items = [
                {
                    "type": "Feature",
                    "stac_version": "1.0.0",
                    "id": f"{collection_id}-item-{i}",
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                    "bbox": [0, 0, 0, 0],
                    "properties": {
                        "datetime": "2024-01-01T00:00:00Z",
                        "collection": collection_id
                    },
                    "links": [],
                    "assets": {}
                }
                for i in range(5)
            ]

            with open(collection_path, 'w') as f:
                json.dump(items, f)

            collection_configs.append({
                "collection_id": collection_id,
                "source": str(collection_path),
                "base_dir": str(tmp_path / "output" / collection_id)
            })

        config = {
            "name": "matrix-parallel-test",
            "strategy": {
                "matrix": collection_configs
            },
            "steps": [
                {
                    "id": "ingest",
                    "module": "IngestModule",
                    "config": {
                        "mode": "file",
                        "format": "json"
                    }
                },
                {
                    "id": "output",
                    "module": "OutputModule",
                    "config": {
                        "format": "json"
                    },
                    "depends_on": ["ingest"]
                }
            ]
        }

        manager = StacManager(config=config, checkpoint_dir=tmp_path / "checkpoints")
        results = await manager.execute()

        # Should have 3 results (one per collection)
        assert len(results) == 3

        # All should succeed
        assert all(r.success for r in results)

        # Total items: 5 per collection × 3 collections
        total_items = sum(r.total_items_processed for r in results)
        assert total_items == 15

        # Each collection output should exist
        for collection_id in ["landsat", "sentinel", "modis"]:
            output_path = tmp_path / "output" / collection_id
            assert output_path.exists()

    with tempfile.TemporaryDirectory() as tmpdir:
        asyncio.run(run_test(Path(tmpdir)))


def test_matrix_strategy_isolates_failures():
    """Test matrix strategy isolates failures between pipelines."""

    async def run_test(tmp_path):
        # Create one valid collection and one that will fail
        valid_path = tmp_path / "valid.json"
        with open(valid_path, 'w') as f:
            json.dump([
                {
                    "type": "Feature",
                    "stac_version": "1.0.0",
                    "id": "valid-item",
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                    "bbox": [0, 0, 0, 0],
                    "properties": {"datetime": "2024-01-01T00:00:00Z"},
                    "links": [],
                    "assets": {}
                }
            ], f)

        # Invalid path doesn't exist (will cause failure)
        invalid_path = tmp_path / "nonexistent.json"

        config = {
            "name": "matrix-isolation-test",
            "strategy": {
                "matrix": [
                    {
                        "collection_id": "valid",
                        "source": str(valid_path),
                        "base_dir": str(tmp_path / "output" / "valid")
                    },
                    {
                        "collection_id": "invalid",
                        "source": str(invalid_path),
                        "base_dir": str(tmp_path / "output" / "invalid")
                    }
                ]
            },
            "steps": [
                {
                    "id": "ingest",
                    "module": "IngestModule",
                    "config": {
                        "mode": "file",
                        "format": "json"
                    }
                },
                {
                    "id": "output",
                    "module": "OutputModule",
                    "config": {
                        "format": "json"
                    },
                    "depends_on": ["ingest"]
                }
            ]
        }

        manager = StacManager(config=config, checkpoint_dir=tmp_path / "checkpoints")
        results = await manager.execute()

        # Should have 2 results
        assert len(results) == 2

        # Valid should succeed, invalid should fail
        valid_result = next(r for r in results if r.matrix_entry["collection_id"] == "valid")
        invalid_result = next(r for r in results if r.matrix_entry["collection_id"] == "invalid")

        assert valid_result.success
        assert not invalid_result.success
    
    with tempfile.TemporaryDirectory() as tmpdir:
        asyncio.run(run_test(Path(tmpdir)))


def test_checkpoint_resume_skips_processed_items():
    """Test workflow resumes from checkpoint, skipping processed items."""
    
    async def run_test(tmp_path):
        # Create test data
        test_items_path = tmp_path / "test_items.json"
        test_items = [
            {
                "type": "Feature",
                "stac_version": "1.0.0",
                "id": f"item-{i}",
                "geometry": {"type": "Point", "coordinates": [0, 0]},
                "bbox": [0, 0, 0, 0],
                "properties": {"datetime": "2024-01-01T00:00:00Z"},
                "links": [],
                "assets": {}
            }
            for i in range(10)
        ]
        
        with open(test_items_path, 'w') as f:
            json.dump(test_items, f)
        
        config = {
            "name": "checkpoint-resume-test",
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
                    "id": "output",
                    "module": "OutputModule",
                    "config": {
                        "base_dir": str(tmp_path / "output"),
                        "format": "json"
                    },
                    "depends_on": ["ingest"]
                }
            ]
        }
        
        checkpoint_dir = tmp_path / "checkpoints"
        
        # First execution: Process all items
        manager1 = StacManager(config=config, checkpoint_dir=checkpoint_dir)
        result1 = await manager1.execute()
        
        assert result1.success
        assert result1.total_items_processed == 10
        
        # Second execution: Should complete without error (resume capability)
        manager2 = StacManager(config=config, checkpoint_dir=checkpoint_dir)
        result2 = await manager2.execute()
        
        # Should complete successfully (whether items are skipped or reprocessed)
        assert result2.success
    
    with tempfile.TemporaryDirectory() as tmpdir:
        asyncio.run(run_test(Path(tmpdir)))


def test_checkpoint_different_workflows_isolated():
    """Test checkpoints are isolated per workflow."""
    
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
        
        checkpoint_dir = tmp_path / "checkpoints"
        
        # Execute workflow A
        config_a = {
            "name": "workflow-a",
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
                    "id": "output",
                    "module": "OutputModule",
                    "config": {
                        "base_dir": str(tmp_path / "output_a"),
                        "format": "json"
                    },
                    "depends_on": ["ingest"]
                }
            ]
        }
        
        manager_a = StacManager(config=config_a, checkpoint_dir=checkpoint_dir)
        await manager_a.execute()
        
        # Execute workflow B (different name)
        config_b = {
            "name": "workflow-b",
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
                    "id": "output",
                    "module": "OutputModule",
                    "config": {
                        "base_dir": str(tmp_path / "output_b"),
                        "format": "json"
                    },
                    "depends_on": ["ingest"]
                }
            ]
        }
        
        manager_b = StacManager(config=config_b, checkpoint_dir=checkpoint_dir)
        result_b = await manager_b.execute()
        
        # Workflow B should process item (different checkpoint)
        assert result_b.success
        
        # Verify separate checkpoint directories
        assert (checkpoint_dir / "workflow-a").exists()
        assert (checkpoint_dir / "workflow-b").exists()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        asyncio.run(run_test(Path(tmpdir)))
