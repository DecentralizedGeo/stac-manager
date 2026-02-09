"""Mock WorkflowContext and infrastructure for module testing."""
from dataclasses import dataclass
from typing import Any
import logging
from stac_manager.core.failures import FailureCollector


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
    failure_collector: FailureCollector
    checkpoints: MockCheckpointManager
    data: dict[str, Any]
    
    @classmethod
    def create(cls, **kwargs):
        """Create mock context with defaults."""
        defaults = {
            'workflow_id': 'test-workflow-001',
            'config': {},
            'logger': logging.getLogger('test'),
            'failure_collector': FailureCollector(),
            'checkpoints': MockCheckpointManager(),
            'data': {}
        }
        defaults.update(kwargs)
        return cls(**defaults)
