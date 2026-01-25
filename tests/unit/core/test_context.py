import pytest
import logging
from pathlib import Path
import tempfile
from stac_manager.core.context import WorkflowContext
from stac_manager.core.failures import FailureCollector
from stac_manager.core.checkpoints import CheckpointManager
from tests.fixtures.context import MockCheckpointManager


def test_workflow_context_creation():
    """WorkflowContext can be created with required fields."""
    ctx = WorkflowContext(
        workflow_id="test-001",
        config={"name": "test"},
        logger=logging.getLogger("test"),
        failure_collector=FailureCollector(),
        checkpoints=MockCheckpointManager(),
        data={"collection_id": "test-collection"}
    )
    
    assert ctx.workflow_id == "test-001"
    assert ctx.config["name"] == "test"
    assert ctx.data["collection_id"] == "test-collection"


def test_failure_collector_add():
    """FailureCollector records failures."""
    collector = FailureCollector()
    
    collector.add(
        item_id="item-001",
        error="Validation failed",
        step_id="validate"
    )
    
    failures = collector.get_all()
    assert len(failures) == 1
    assert failures[0].item_id == "item-001"
    assert failures[0].error_type == "str"
    assert failures[0].message == "Validation failed"


def test_failure_collector_with_exception():
    """FailureCollector handles Exception objects."""
    collector = FailureCollector()
    
    try:
        raise ValueError("Test error")
    except ValueError as e:
        collector.add(
            item_id="item-002",
            error=e,
            step_id="transform"
        )
    
    failures = collector.get_all()
    assert len(failures) == 1
    assert failures[0].error_type == "ValueError"
    assert "Test error" in failures[0].message


def test_workflow_context_with_checkpoint_manager():
    """Test WorkflowContext includes CheckpointManager."""
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_manager = CheckpointManager(
            directory=Path(tmpdir),
            workflow_id="test-workflow",
            step_id="step1"
        )
        
        context = WorkflowContext(
            workflow_id="test-workflow",
            config={},
            logger=logging.getLogger("test"),
            failure_collector=FailureCollector(),
            checkpoints=checkpoint_manager,
            data={}
        )
        
        assert context.checkpoints is checkpoint_manager
        assert isinstance(context.checkpoints, CheckpointManager)


def test_workflow_context_fork_shares_checkpoint_manager():
    """Test that forked contexts share the same CheckpointManager."""
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_manager = CheckpointManager(
            directory=Path(tmpdir),
            workflow_id="test-workflow",
            step_id="step1"
        )
        
        parent_context = WorkflowContext(
            workflow_id="test-workflow",
            config={},
            logger=logging.getLogger("test"),
            failure_collector=FailureCollector(),
            checkpoints=checkpoint_manager,
            data={"parent_key": "parent_value"}
        )
        
        # Fork context
        child_context = parent_context.fork(data={"child_key": "child_value"})
        
        # Should share same checkpoint manager
        assert child_context.checkpoints is parent_context.checkpoints
        
        # Should have merged data
        assert child_context.data["parent_key"] == "parent_value"
        assert child_context.data["child_key"] == "child_value"

