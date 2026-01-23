import pytest
from stac_manager.protocols import Fetcher, Modifier, Bundler
from stac_manager.core.context import WorkflowContext
from tests.fixtures.context import MockWorkflowContext


class MockFetcher:
    """Mock Fetcher implementation for testing."""
    
    def __init__(self, config: dict) -> None:
        self.config = config
    
    async def fetch(self, context: WorkflowContext):
        yield {"id": "test-001"}


def test_fetcher_protocol_compliance():
    """MockFetcher implements Fetcher protocol."""
    fetcher = MockFetcher({"test": True})
    
    # Protocol check (runtime checkable)
    assert isinstance(fetcher, Fetcher)
    assert hasattr(fetcher, 'fetch')
