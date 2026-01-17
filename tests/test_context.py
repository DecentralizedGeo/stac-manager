import logging
from stac_manager.context import WorkflowContext
from stac_manager.failures import FailureCollector

def test_context_init():
    # Mocking checkpointer for now as Any
    ctx = WorkflowContext(
        workflow_id="test-flow",
        config={},  # type: ignore
        logger=logging.getLogger(),
        failure_collector=FailureCollector(),
        checkpoints=None, # type: ignore
        data={}
    )
    assert ctx.workflow_id == "test-flow"
    assert ctx.data == {}
