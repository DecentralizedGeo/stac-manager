from stac_manager.utils import validate_workflow_config

def test_validate_valid_config():
    config = {
        "name": "test-wf",
        "description": "valid config",
        "steps": [
            {"id": "step1", "module": "Discovery", "config": {}},
            {"id": "step2", "module": "Ingest", "config": {}, "depends_on": ["step1"]}
        ]
    }
    errors = validate_workflow_config(config)
    assert len(errors) == 0

def test_validate_circular_dependency():
    config = {
        "name": "cycle",
        "steps": [
            {"id": "A", "module": "M", "config": {}, "depends_on": ["B"]},
            {"id": "B", "module": "M", "config": {}, "depends_on": ["A"]}
        ]
    }
    errors = validate_workflow_config(config)
    assert any("Circular" in e for e in errors)

def test_validate_missing_dependency():
    config = {
        "name": "missing",
        "steps": [
            {"id": "A", "module": "M", "config": {}, "depends_on": ["Z"]}
        ]
    }
    errors = validate_workflow_config(config)
    assert any("unknown step: Z" in e for e in errors)
