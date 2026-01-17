import pytest
from unittest.mock import MagicMock, patch
from stac_manager.manager import StacManager
from stac_manager.config import WorkflowDefinition

@pytest.mark.asyncio
async def test_manager_simple_flow():
    config = WorkflowDefinition(
        name="test",
        steps=[
            {"id": "step1", "module": "DiscoveryModule", "config": {"url": "http://foo"}}
        ]
    )
    
    # Mock MODULE_REGISTRY and dynamic import
    with patch('stac_manager.manager.get_module_class') as mock_get_cls:
        # Mock module instance
        mock_instance = MagicMock()
        
        # Async generator for fetch
        async def async_gen(ctx):
            yield {"id": "item1"}
        
        mock_instance.fetch = MagicMock(side_effect=async_gen)
        mock_get_cls.return_value = MagicMock(return_value=mock_instance)
        
        manager = StacManager(config)
        result = await manager.execute()
        
        assert result['success'] is True
        assert result['failure_count'] == 0
        
        # Verify execution
        mock_instance.fetch.assert_called_once()
