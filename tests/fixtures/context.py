"""Mock WorkflowContext and infrastructure for module testing."""
from dataclasses import dataclass
from typing import Any
import logging


@dataclass
class MockFailureCollector:
    """Mock FailureCollector for testing."""
    failures: list[dict]
    
    def __init__(self):
        self.failures = []
    
    def add(self, item_id: str, error: str | Exception, step_id: str = 'unknown', error_context: dict | None = None) -> None:
        from collections import namedtuple
        Record = namedtuple('Record', ['item_id', 'message', 'step_id', 'context', 'error_type'])
        self.failures.append(Record(
            item_id=item_id,
            message=str(error),
            step_id=step_id,
            context=error_context,
            error_type="str"
        ))

    def get_all(self):
        return self.failures


@dataclass
class MockCheckpointManager:
    """Mock CheckpointManager for testing."""
    
    def save(self, state: dict) -> None:
        pass
    
    def load(self) -> dict | None:
        return None


@dataclass
class MockWorkflowContext:
    """Mock WorkflowContext for module testing."""
    workflow_id: str
    config: dict
    logger: logging.Logger
    failure_collector: MockFailureCollector
    checkpoints: MockCheckpointManager
    data: dict[str, Any]
    
    @classmethod
    def create(cls, **kwargs):
        """Create mock context with defaults."""
        defaults = {
            'workflow_id': 'test-workflow-001',
            'config': {},
            'logger': logging.getLogger('test'),
            'failure_collector': MockFailureCollector(),
            'checkpoints': MockCheckpointManager(),
            'data': {}
        }
        defaults.update(kwargs)
        return cls(**defaults)
