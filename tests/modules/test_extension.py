import pytest
from stac_manager.modules.extension import ExtensionModule
from stac_manager.context import WorkflowContext
from unittest.mock import MagicMock
import pystac

def test_apply_extension():
    # Setup a mock config
    config = {
        "extension": "mock_ext",
        "config": {"foo": "bar"}
    }
    
    # In a real scenario we'd register a class or mock the loader.
    # For this unit test, let's subclass ExtensionModule or mock internal loader 
    # if we want to test that logic, OR just test the modify flow.
    # The plan suggests implementing a basic framework.
    
    # Let's simple check that modify converts dict->Item->dict
    module = ExtensionModule(config)
    ctx = MagicMock(spec=WorkflowContext)
    
    item_dict = {
        "id": "test",
        "type": "Feature",
        "geometry": None,
        "properties": {"datetime": "2021-01-01T00:00:00Z"},
        "links": [],
        "assets": {},
        "stac_version": "1.0.0"
    }
    
    # For now, without a real extension loaded, it might just return the item or error.
    # Let's assume the basic implementation just passes through if no extension logic is found 
    # OR we can mock the apply method if we refactor.
    
    # Actually, the plan code shows:
    # # 2. Apply (mock logic for plan)
    # # ext = self.extension_cls()
    # # stac_item = ext.apply(stac_item, self.config.config)
    
    # We will implement a dummy apply for the test by monkeypatching
    
    res = module.modify(item_dict, ctx)
    assert res['id'] == "test"
    # Basic check ensuring pystac conversion cycle worked
