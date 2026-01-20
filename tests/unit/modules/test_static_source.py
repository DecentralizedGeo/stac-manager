import pytest
import asyncio
from stac_manager.modules.static_source import StaticSourceModule, StaticSourceConfig

@pytest.mark.asyncio
async def test_static_source_yields_items():
    config = {
        "items": [
            {"id": "item1", "type": "Feature"},
            {"id": "item2", "type": "Feature"}
        ]
    }
    module = StaticSourceModule(config)
    items = []
    async for item in module.fetch(None):
        items.append(item)
    
    assert len(items) == 2
    assert items[0]["id"] == "item1"
    assert items[1]["id"] == "item2"
