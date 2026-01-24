"""Workflow execution context."""
from dataclasses import dataclass
from typing import Any
import logging
from stac_manager.core.failures import FailureCollector


@dataclass
class WorkflowContext:
    """Shared state passed to all components during execution."""
    workflow_id: str
    config: dict
    logger: logging.Logger
    failure_collector: FailureCollector
    checkpoints: 'CheckpointManager'
    data: dict[str, Any]
    
    def fork(self, data: dict[str, Any]) -> 'WorkflowContext':
        """
        Create a child context with isolated data.
        Used for Matrix Strategy to spawn parallel pipelines.
        """
        return WorkflowContext(
            workflow_id=self.workflow_id,
            config=self.config,
            logger=self.logger,
            failure_collector=self.failure_collector,
            checkpoints=self.checkpoints,
            data={**self.data, **data}
        )
