import pytest
from stac_manager.modules.seed import SeedModule
from tests.fixtures.context import MockWorkflowContext
from tests.fixtures.modules import SEED_CONFIG_BASIC


@pytest.mark.asyncio
async def test_seed_module_yields_string_items():
    """SeedModule yields items from string list."""
    module = SeedModule(SEED_CONFIG_BASIC)
    context = MockWorkflowContext.create()
    
    items = []
    async for item in module.fetch(context):
        items.append(item)
    
    assert len(items) == 3
    assert items[0]["id"] == "item-001"
    assert items[1]["id"] == "item-002"
    assert items[2]["id"] == "item-003"


from tests.fixtures.modules import SEED_CONFIG_WITH_DEFAULTS


@pytest.mark.asyncio
async def test_seed_module_applies_defaults():
    """SeedModule applies default values to items."""
    module = SeedModule(SEED_CONFIG_WITH_DEFAULTS)
    context = MockWorkflowContext.create()
    
    items = []
    async for item in module.fetch(context):
        items.append(item)
    
    # First item (string) gets full defaults
    assert items[0]["id"] == "item-001"
    assert items[0]["collection"] == "test-collection"
    assert items[0]["properties"]["instrument"] == "OLI"
    
    # Second item (dict) merges with defaults
    assert items[1]["id"] == "item-002"
    assert items[1]["collection"] == "test-collection"
    assert items[1]["properties"]["platform"] == "Landsat-8"  # Item-specific
    assert items[1]["properties"]["instrument"] == "OLI"  # From defaults


@pytest.mark.asyncio
async def test_seed_module_context_enrichment():
    """SeedModule enriches items from context.data."""
    module = SeedModule({"items": ["item-001"]})
    context = MockWorkflowContext.create(
        data={"collection_id": "landsat-c2"}
    )
    
    items = []
    async for item in module.fetch(context):
        items.append(item)
    
    assert items[0]["collection"] == "landsat-c2"


import tempfile
import json


@pytest.mark.asyncio
async def test_seed_module_loads_from_file():
    """SeedModule loads items from source_file."""
    # Create temp JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(["file-item-001", "file-item-002"], f)
        temp_path = f.name
    
    try:
        module = SeedModule({"source_file": temp_path})
        context = MockWorkflowContext.create()
        
        items = []
        async for item in module.fetch(context):
            items.append(item)
        
        assert len(items) == 2
        assert items[0]["id"] == "file-item-001"
        assert items[1]["id"] == "file-item-002"
    finally:
        import os
        os.unlink(temp_path)


from stac_manager.protocols import Fetcher


def test_seed_module_protocol_compliance():
    """SeedModule implements Fetcher protocol."""
    module = SeedModule(SEED_CONFIG_BASIC)
    assert isinstance(module, Fetcher)




