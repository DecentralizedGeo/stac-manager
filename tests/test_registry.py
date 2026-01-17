import pytest
from stac_manager.registry import get_module_class
from stac_manager.exceptions import WorkflowConfigError

def test_get_unknown_module():
    with pytest.raises(WorkflowConfigError):
        get_module_class("UnknownModule")
