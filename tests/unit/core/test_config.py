"""Tests for workflow configuration models."""
import pytest
from pathlib import Path
import tempfile
from stac_manager.core.config import (
    WorkflowDefinition,
    StepConfig,
    StrategyConfig,
    load_workflow_from_yaml,
    build_execution_order
)
from stac_manager.exceptions import ConfigurationError


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


def test_load_workflow_from_yaml_valid():
    """Test loading valid YAML workflow configuration."""
    yaml_content = """
name: test-workflow
description: Test workflow
version: "1.0"

steps:
  - id: ingest
    module: IngestModule
    config:
      collection_id: landsat-c2-l2
      
  - id: output
    module: OutputModule
    config:
      output_path: ./data/output
    depends_on:
      - ingest
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        yaml_path = Path(f.name)
    
    try:
        workflow = load_workflow_from_yaml(yaml_path)
        
        assert workflow.name == "test-workflow"
        assert workflow.description == "Test workflow"
        assert len(workflow.steps) == 2
        
        # Verify first step
        assert workflow.steps[0].id == "ingest"
        assert workflow.steps[0].module == "IngestModule"
        assert workflow.steps[0].config["collection_id"] == "landsat-c2-l2"
        
        # Verify second step
        assert workflow.steps[1].id == "output"
        assert workflow.steps[1].depends_on == ["ingest"]
    finally:
        yaml_path.unlink()


def test_load_workflow_from_yaml_invalid_structure():
    """Test loading YAML with invalid structure raises error."""
    yaml_content = """
name: test-workflow
steps:
  - id: invalid_step
    # Missing required 'module' field
    config: {}
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        yaml_path = Path(f.name)
    
    try:
        with pytest.raises(ConfigurationError) as exc_info:
            load_workflow_from_yaml(yaml_path)
        
        assert "module" in str(exc_info.value).lower()
    finally:
        yaml_path.unlink()


def test_load_workflow_from_yaml_file_not_found():
    """Test loading non-existent file raises error."""
    with pytest.raises(ConfigurationError) as exc_info:
        load_workflow_from_yaml(Path("/nonexistent/workflow.yaml"))
    
    assert "not found" in str(exc_info.value).lower()


def test_build_execution_order_linear():
    """Test DAG resolution for simple linear pipeline."""
    steps = [
        StepConfig(id="step1", module="IngestModule", config={}),
        StepConfig(id="step2", module="UpdateModule", config={}, depends_on=["step1"]),
        StepConfig(id="step3", module="OutputModule", config={}, depends_on=["step2"])
    ]
    
    order = build_execution_order(steps)
    
    assert order == ["step1", "step2", "step3"]


def test_build_execution_order_parallel_branches():
    """Test DAG resolution with parallel branches that converge."""
    steps = [
        StepConfig(id="ingest", module="IngestModule", config={}),
        StepConfig(id="transform_a", module="TransformModule", config={}, depends_on=["ingest"]),
        StepConfig(id="transform_b", module="UpdateModule", config={}, depends_on=["ingest"]),
        StepConfig(id="validate", module="ValidateModule", config={}, depends_on=["transform_a", "transform_b"]),
        StepConfig(id="output", module="OutputModule", config={}, depends_on=["validate"])
    ]
    
    order = build_execution_order(steps)
    
    # Verify ordering constraints
    assert order.index("ingest") < order.index("transform_a")
    assert order.index("ingest") < order.index("transform_b")
    assert order.index("transform_a") < order.index("validate")
    assert order.index("transform_b") < order.index("validate")
    assert order.index("validate") < order.index("output")
    
    # Verify all steps included
    assert set(order) == {"ingest", "transform_a", "transform_b", "validate", "output"}


def test_build_execution_order_no_dependencies():
    """Test single step with no dependencies."""
    steps = [
        StepConfig(id="only_step", module="IngestModule", config={})
    ]
    
    order = build_execution_order(steps)
    
    assert order == ["only_step"]


def test_build_execution_order_detects_simple_cycle():
    """Test cycle detection for simple A -> B -> A cycle."""
    steps = [
        StepConfig(id="step_a", module="UpdateModule", config={}, depends_on=["step_b"]),
        StepConfig(id="step_b", module="TransformModule", config={}, depends_on=["step_a"])
    ]
    
    with pytest.raises(ConfigurationError) as exc_info:
        build_execution_order(steps)
    
    assert "circular dependency" in str(exc_info.value).lower()


def test_build_execution_order_detects_complex_cycle():
    """Test cycle detection for longer cycle A -> B -> C -> A."""
    steps = [
        StepConfig(id="step_a", module="IngestModule", config={}, depends_on=["step_c"]),
        StepConfig(id="step_b", module="TransformModule", config={}, depends_on=["step_a"]),
        StepConfig(id="step_c", module="UpdateModule", config={}, depends_on=["step_b"])
    ]
    
    with pytest.raises(ConfigurationError) as exc_info:
        build_execution_order(steps)
    
    assert "circular dependency" in str(exc_info.value).lower()


def test_build_execution_order_missing_dependency():
    """Test error when step depends on non-existent step."""
    steps = [
        StepConfig(id="step1", module="IngestModule", config={}),
        StepConfig(id="step2", module="OutputModule", config={}, depends_on=["nonexistent"])
    ]
    
    with pytest.raises(ConfigurationError) as exc_info:
        build_execution_order(steps)
    
    assert "unknown step" in str(exc_info.value).lower()
    assert "nonexistent" in str(exc_info.value)
