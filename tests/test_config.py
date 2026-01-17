from stac_manager.config import WorkflowDefinition, StepConfig
import pytest

def test_workflow_validation():
    data = {
        "name": "test-workflow",
        "settings": {
            "logging": {"level": "DEBUG"}
        },
        "steps": [
            {"id": "step1", "module": "Discovery", "config": {"url": "http://foo"}}
        ]
    }
    wf = WorkflowDefinition(**data)
    assert wf.name == "test-workflow"
    assert wf.steps[0].id == "step1"
    assert wf.settings.logging.level == "DEBUG"

def test_missing_steps():
    with pytest.raises(ValueError):
        WorkflowDefinition(name="bad")
