"""Tests for StacManager orchestration."""
import pytest
from pathlib import Path
import logging
from stac_manager.core.manager import MODULE_REGISTRY, load_module_class, StacManager
from stac_manager.core.config import WorkflowDefinition, StepConfig
from stac_manager.exceptions import ConfigurationError


def test_module_registry_contains_all_modules():
    """Test MODULE_REGISTRY contains all implemented modules."""
    expected_modules = [
        'IngestModule',
        'SeedModule',
        'TransformModule',
        'UpdateModule',
        'ExtensionModule',
        'ValidateModule',
        'OutputModule'
    ]
    
    for module_name in expected_modules:
        assert module_name in MODULE_REGISTRY


def test_load_module_class_valid():
    """Test loading a valid module class."""
    module_class = load_module_class('IngestModule')
    
    # Verify it's a class (not instance)
    assert isinstance(module_class, type)
    
    # Verify class name
    assert module_class.__name__ == 'IngestModule'


def test_load_module_class_invalid():
    """Test loading an unknown module raises error."""
    with pytest.raises(ConfigurationError) as exc_info:
        load_module_class('NonExistentModule')
    
    assert "unknown module" in str(exc_info.value).lower()
    assert "NonExistentModule" in str(exc_info.value)


def test_load_module_class_all_registered():
    """Test that all registered modules can be loaded."""
    for module_name in MODULE_REGISTRY.keys():
        module_class = load_module_class(module_name)
        assert module_class is not None
        assert module_class.__name__ == module_name


def test_stac_manager_initialization_from_dict():
    """Test StacManager initialization with dict configuration."""
    config = {
        "name": "test-workflow",
        "steps": [
            {
                "id": "ingest",
                "module": "IngestModule",
                "config": {"collection_id": "test"}
            }
        ]
    }
    
    manager = StacManager(config=config)
    
    assert manager.workflow.name == "test-workflow"
    assert len(manager.workflow.steps) == 1
    assert manager.workflow.steps[0].id == "ingest"


def test_stac_manager_initialization_from_workflow_definition():
    """Test StacManager initialization with WorkflowDefinition."""
    workflow = WorkflowDefinition(
        name="test-workflow",
        steps=[
            StepConfig(id="ingest", module="IngestModule", config={})
        ]
    )
    
    manager = StacManager(config=workflow)
    
    assert manager.workflow is workflow
    assert manager.workflow.name == "test-workflow"


def test_stac_manager_validates_execution_order():
    """Test StacManager validates and builds execution order."""
    config = {
        "name": "test-workflow",
        "steps": [
            {"id": "step2", "module": "UpdateModule", "config": {}, "depends_on": ["step1"]},
            {"id": "step1", "module": "IngestModule", "config": {}}
        ]
    }
    
    manager = StacManager(config=config)
    
    # Should resolve correct order despite definition order
    execution_order = manager._execution_order
    assert execution_order == ["step1", "step2"]


def test_stac_manager_detects_circular_dependencies():
    """Test StacManager detects cycles during initialization."""
    config = {
        "name": "test-workflow",
        "steps": [
            {"id": "step_a", "module": "UpdateModule", "config": {}, "depends_on": ["step_b"]},
            {"id": "step_b", "module": "TransformModule", "config": {}, "depends_on": ["step_a"]}
        ]
    }
    
    with pytest.raises(ConfigurationError) as exc_info:
        StacManager(config=config)
    
    assert "circular dependency" in str(exc_info.value).lower()
