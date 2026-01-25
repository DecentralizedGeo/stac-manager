"""Tests for workflow configuration models."""
import pytest
from stac_manager.core.config import WorkflowDefinition, StepConfig, StrategyConfig


def test_step_config_minimal():
    """Test StepConfig with minimal required fields."""
    step = StepConfig(
        id="test_step",
        module="IngestModule",
        config={"collection_id": "test"}
    )
    
    assert step.id == "test_step"
    assert step.module == "IngestModule"
    assert step.config == {"collection_id": "test"}
    assert step.depends_on == []  # Default empty list


def test_step_config_with_dependencies():
    """Test StepConfig with dependencies."""
    step = StepConfig(
        id="transform",
        module="TransformModule",
        config={},
        depends_on=["ingest", "seed"]
    )
    
    assert step.depends_on == ["ingest", "seed"]


def test_workflow_definition_minimal():
    """Test WorkflowDefinition with minimal configuration."""
    workflow = WorkflowDefinition(
        name="test-workflow",
        steps=[
            StepConfig(id="step1", module="IngestModule", config={})
        ]
    )
    
    assert workflow.name == "test-workflow"
    assert workflow.version == "1.0"  # Default
    assert workflow.description is None
    assert len(workflow.steps) == 1
    assert workflow.strategy.matrix is None  # Default no matrix
