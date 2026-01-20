import pytest
import asyncio
from unittest.mock import MagicMock, patch
from stac_manager.manager import StacManager
from stac_manager.config import WorkflowDefinition, StepConfig

# Mock modules
class MockProducer:
    def __init__(self, config): pass
    async def fetch(self, context):
        yield {"task": "dummy_task"}

class MockConsumer:
    def __init__(self, config): pass
    # Accepts 'items' argument! This is what we are testing.
    async def fetch(self, context, items=None):
        if items:
            async for item in items:
                yield {"result": item["task"] + "_processed"}

@pytest.mark.asyncio
async def test_manager_passes_fetch_input():
    # Setup Config
    config = WorkflowDefinition(
        name="handoff-test",
        settings={}, # Pass empty dict for default settings
        steps=[
            StepConfig(id="step1", module="tests.unit.test_manager_handoff.MockProducer", config={}),
            StepConfig(id="step2", module="tests.unit.test_manager_handoff.MockConsumer", config={}, depends_on=["step1"])
        ]
    )
    
    manager = StacManager(config)
    # Patch registry to return our mocks
    with patch("stac_manager.manager.get_module_class") as mock_get:
        mock_get.side_effect = lambda name: MockProducer if "Producer" in name else MockConsumer
        
        # Execute
        await manager.execute()
        
    # Verify Step 2 received data and processed it
    # We check context.data for the result of step 2
    results = manager.context.data["step2"]
    
    # Iterate results (handling both list and async iterator possibilities during refactor)
    processed = []
    if hasattr(results, "__aiter__"):
        async for i in results:
            processed.append(i)
    else:
        processed = results
    
    assert len(processed) == 1
    assert processed[0]["result"] == "dummy_task_processed"
