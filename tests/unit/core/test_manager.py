"""Tests for StacManager orchestration."""
import pytest
import asyncio
import tempfile
import json
from pathlib import Path
import logging
from stac_manager.core.manager import MODULE_REGISTRY, load_module_class, StacManager
from stac_manager.core.config import WorkflowDefinition, StepConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.protocols import Fetcher, Modifier, Bundler
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


def test_stac_manager_instantiates_modules():
    """Test StacManager instantiates all modules for workflow."""
    config = {
        "name": "test-workflow",
        "steps": [
            {
                "id": "ingest", 
                "module": "IngestModule", 
                "config": {
                    "mode": "api",
                    "source": "https://test.example.com/api",
                    "collection_id": "test"
                }
            },
            {"id": "update", "module": "UpdateModule", "config": {"fields": {}}, "depends_on": ["ingest"]},
            {"id": "output", "module": "OutputModule", "config": {"base_dir": "./output", "format": "json"}, "depends_on": ["update"]}
        ]
    }
    
    manager = StacManager(config=config)
    
    # Create mock context for instantiation
    context = WorkflowContext(
        workflow_id="test-workflow",
        config={},
        logger=manager.logger,
        failure_collector=None,  # Will be created by manager
        checkpoints=None,  # Will be created by manager
        data={}
    )
    
    # Instantiate modules
    modules = manager._instantiate_modules(context)
    
    # Verify all modules instantiated
    assert "ingest" in modules
    assert "update" in modules
    assert "output" in modules
    
    # Verify protocol compliance
    assert isinstance(modules["ingest"], Fetcher)
    assert isinstance(modules["update"], Modifier)
    assert isinstance(modules["output"], Bundler)


def test_stac_manager_module_instantiation_with_config():
    """Test modules receive their configuration."""
    config = {
        "name": "test-workflow",
        "steps": [
            {
                "id": "ingest",
                "module": "IngestModule",
                "config": {
                    "mode": "api",
                    "source": "https://test.example.com/api",
                    "collection_id": "test-collection"
                }
            }
        ]
    }
    
    manager = StacManager(config=config)
    
    context = WorkflowContext(
        workflow_id="test-workflow",
        config={},
        logger=manager.logger,
        failure_collector=None,
        checkpoints=None,
        data={}
    )
    
    modules = manager._instantiate_modules(context)
    
    # Verify module has config
    ingest_module = modules["ingest"]
    assert ingest_module.config.source == "https://test.example.com/api"
    assert ingest_module.config.collection_id == "test-collection"


@pytest.mark.asyncio
async def test_stac_manager_execute_simple_pipeline(tmp_path):
    """Test StacManager executes a simple pipeline."""
    # Create test data file
    test_data_path = tmp_path / "test_items.json"
    test_items = [
        {
            "type": "Feature",
            "stac_version": "1.0.0",
            "id": "test-item-1",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
            "bbox": [0, 0, 0, 0],
            "properties": {"datetime": "2024-01-01T00:00:00Z"},
            "links": [],
            "assets": {}
        }
    ]
    
    with open(test_data_path, 'w') as f:
        json.dump(test_items, f)
    
    # Create workflow
    config = {
        "name": "simple-pipeline",
        "steps": [
            {
                "id": "ingest",
                "module": "IngestModule",
                "config": {"mode": "file", "source": str(test_data_path), "format": "json"}
            },
            {
                "id": "output",
                "module": "OutputModule",
                "config": {"base_dir": str(tmp_path / "output"), "format": "json"},
                "depends_on": ["ingest"]
            }
        ]
    }
    
    manager = StacManager(config=config, checkpoint_dir=tmp_path / "checkpoints")
    
    # Execute pipeline
    result = await manager.execute()
    
    # Verify execution succeeded
    assert result.success is True
    assert result.failure_count == 0
    assert result.total_items_processed == 1


@pytest.mark.asyncio
async def test_stac_manager_matrix_strategy_note():
    """Test documenting that matrix strategy requires config merging, not variable substitution."""
    # NOTE: Variable substitution (${var}) is deferred to v1.1
    # Matrix strategy in v1.0 works by merging matrix entry data into step configs directly
    # This means you need to structure your workflow to accept matrix data as direct config values
    
    # Example: Instead of {"source": "${source_file}"}, use empty config and rely on context.data
    # The manager will merge matrix entry data into step config during instantiation
    
    config = {
        "name": "matrix-note",
        "strategy": {
            "matrix": [
                {"note": "Matrix v1.0 uses direct config merging"}
            ]
        },
        "steps": []
    }
    
    # This is a documentation test - no actual execution needed
    manager = StacManager(config=config)
    assert manager.workflow.strategy.matrix is not None
