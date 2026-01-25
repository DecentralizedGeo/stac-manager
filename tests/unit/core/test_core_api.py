"""Tests for core module public API."""
import pytest


def test_core_imports():
    """Test that core components are importable from stac_manager.core."""
    from stac_manager.core import (
        WorkflowContext,
        FailureCollector,
        FailureRecord,
        WorkflowDefinition,
        StepConfig,
        StrategyConfig,
        load_workflow_from_yaml,
        build_execution_order
    )
    
    # Verify classes are importable
    assert WorkflowContext is not None
    assert FailureCollector is not None
    assert FailureRecord is not None
    assert WorkflowDefinition is not None
    assert StepConfig is not None
    assert StrategyConfig is not None
    
    # Verify functions are callable
    assert callable(load_workflow_from_yaml)
    assert callable(build_execution_order)
