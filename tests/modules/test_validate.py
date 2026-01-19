from stac_manager.modules.validate import ValidateModule
from stac_manager.context import WorkflowContext
from unittest.mock import MagicMock, patch

def test_validate_valid_item():
    module = ValidateModule({"strict": True})
    ctx = MagicMock(spec=WorkflowContext)
    ctx.logger = MagicMock()
    ctx.data = {}
    
    valid_item = {
        "id": "test",
        "type": "Feature",
        "geometry": None,
        "properties": {"datetime": "2021-01-01T00:00:00Z"},
        "links": [],
        "assets": {},
        "stac_version": "1.0.0"
    }
    
    with patch("stac_manager.modules.validate.stac_validator.StacValidate") as MockVal:
        instance = MockVal.return_value
        instance.validate_dict.return_value = True
        
        res = module.modify(valid_item, ctx)
        assert res == valid_item
