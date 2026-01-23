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
