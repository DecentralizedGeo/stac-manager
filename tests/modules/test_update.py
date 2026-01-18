from stac_manager.modules.update import UpdateModule
from stac_manager.context import WorkflowContext
from unittest.mock import MagicMock

def test_update_item_field():
    config = {
        "mode": "merge",
        "updates": {
            "properties.title": "New Title",
            "assets.thumbnail.title": "New Thumb"
        }
    }
    module = UpdateModule(config)
    ctx = MagicMock(spec=WorkflowContext)
    
    item = {
        "id": "1",
        "properties": {"title": "Old"},
        "assets": {"thumbnail": {"href": "img.jpg", "title": "Old"}}
    }
    
    result = module.modify(item, ctx)
    assert result['properties']['title'] == "New Title"
    assert result['assets']['thumbnail']['title'] == "New Thumb"
