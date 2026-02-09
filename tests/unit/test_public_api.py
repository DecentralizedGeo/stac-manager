"""Tests for top-level stac_manager public API."""
import pytest


def test_top_level_imports():
    """Test that core components are importable from stac_manager directly."""
    from stac_manager import StacManager, load_workflow_from_yaml
    
    assert StacManager is not None
    assert callable(load_workflow_from_yaml)


@pytest.mark.asyncio
async def test_stac_manager_programmatic_usage():
    """Test StacManager can be used programmatically."""
    from stac_manager import StacManager
    
    config = {
        "name": "programmatic-test",
        "steps": [
            {
                "id": "seed",
                "module": "SeedModule",
                "config": {
                    "items": [
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
                }
            }
        ]
    }
    
    manager = StacManager(config=config)
    
    # Should be able to access workflow
    assert manager.workflow.name == "programmatic-test"
