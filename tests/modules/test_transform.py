from stac_manager.modules.transform import TransformModule, TransformConfig
from stac_manager.context import WorkflowContext
from unittest.mock import MagicMock

def test_transform_simple():
    config = {
        "mappings": [
            {"source_field": "foo", "target_field": "id", "type": "string"},
            {"source_field": "meta.dt", "target_field": "properties.datetime", "type": "string"}
        ]
    }
    module = TransformModule(config)
    ctx = MagicMock(spec=WorkflowContext)
    
    item = {"foo": "item-1", "meta": {"dt": "2024-01-01"}}
    result = module.modify(item, ctx)
    
    assert result['id'] == "item-1"
    assert result['properties']['datetime'] == "2024-01-01"
