from stac_manager.modules.scaffold import ScaffoldModule, ScaffoldConfig
from stac_manager.context import WorkflowContext
from unittest.mock import MagicMock
import pystac

def test_scaffold_item_creation():
    config = {
        "mode": "items",
        "defaults": {
            "license": "CC-BY-4.0",
            "providers": [{"name": "MyProvider", "roles": ["host"]}]
        }
    }
    module = ScaffoldModule(config)
    ctx = MagicMock(spec=WorkflowContext)
    ctx.logger = MagicMock()
    ctx.data = {}  # Input data (e.g. from Transform)
    input_data = {
        "id": "item-1",
        "properties": {"datetime": "2024-01-01T00:00:00Z"},
        "geometry": {"type": "Point", "coordinates": [0, 0]}
    }
    
    result = module.modify(input_data, ctx)
    
    # Check basics
    assert result['id'] == "item-1"
    assert result['type'] == "Feature"
    assert result['stac_version'] == pystac.get_stac_version()
    # Check datetime parsing happened (pystac converts to string in to_dict typically, 
    # but let's verify it persisted)
    assert result['properties']['datetime'] == "2024-01-01T00:00:00Z"
