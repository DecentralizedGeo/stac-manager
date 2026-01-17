from dataclasses import dataclass
from typing import Any, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from stac_manager.failures import FailureCollector
    # CheckpointManager deferred for later task

@dataclass
class WorkflowContext:
    """Shared state passed to all components during execution."""
    workflow_id: str
    config: Any  # WorkflowDefinition typed later to avoid circular import
    logger: logging.Logger
    failure_collector: 'FailureCollector'
    checkpoints: Any # CheckpointManager
    data: dict[str, Any]
