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

