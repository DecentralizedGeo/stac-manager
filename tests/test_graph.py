import pytest
from stac_manager.graph import build_execution_levels
from stac_manager.config import StepConfig

def test_dag_simple():
    steps = [
        StepConfig(id="A", module="M", config={}),
        StepConfig(id="B", module="M", config={}, depends_on=["A"]),
        StepConfig(id="C", module="M", config={}, depends_on=["B"]),
    ]
    levels = build_execution_levels(steps)
    assert levels == [["A"], ["B"], ["C"]]

def test_dag_cycle():
    steps = [
        StepConfig(id="A", module="M", config={}, depends_on=["B"]),
        StepConfig(id="B", module="M", config={}, depends_on=["A"]),
    ]
    with pytest.raises(Exception): # WorkflowConfigError
        build_execution_levels(steps)
