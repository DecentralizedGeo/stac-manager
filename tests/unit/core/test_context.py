import pytest
import logging
from stac_manager.core.context import WorkflowContext
from tests.fixtures.context import MockFailureCollector, MockCheckpointManager


def test_workflow_context_creation():
    """WorkflowContext can be created with required fields."""
    ctx = WorkflowContext(
        workflow_id="test-001",
        config={"name": "test"},
        logger=logging.getLogger("test"),
        failure_collector=MockFailureCollector(),
        checkpoints=MockCheckpointManager(),
        data={"collection_id": "test-collection"}
    )
    
    assert ctx.workflow_id == "test-001"
    assert ctx.config["name"] == "test"
    assert ctx.data["collection_id"] == "test-collection"


from stac_manager.core.failures import FailureCollector, FailureRecord


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

