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
