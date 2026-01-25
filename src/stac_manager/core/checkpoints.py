"""Checkpoint management for workflow state persistence."""
from pathlib import Path
from typing import TypedDict


class CheckpointRecord(TypedDict):
    """Single checkpoint record."""
    item_id: str
    step_id: str
    timestamp: str  # ISO 8601
    status: str  # 'success' or 'failure'


class CheckpointManager:
    """
    Manages persistence of processing state using Parquet files.
    
    Uses partitioned writes to avoid rewriting large files.
    Directory structure: {directory}/{workflow_id}/{step_id}/
    """
    
    def __init__(
        self,
        directory: Path,
        workflow_id: str,
        step_id: str | None = None
    ):
        """
        Initialize manager and load existing checkpoint state.
        
        Args:
            directory: Base checkpoint directory
            workflow_id: Unique workflow identifier
            step_id: Step identifier (None for workflow-level manager)
        """
        self.directory = directory
        self.workflow_id = workflow_id
        self.step_id = step_id or "global"
        
        # Build checkpoint path
        self._checkpoint_path = self.directory / self.workflow_id / self.step_id
        
        # Create directory if missing
        self._checkpoint_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing state
        self._processed_items: set[str] = set()
        self._load_checkpoint_state()
    
    def get_checkpoint_path(self) -> Path:
        """Return full path to checkpoint directory."""
        return self._checkpoint_path
    
    def contains(self, item_id: str) -> bool:
        """
        Check if an item has already been processed.
        
        Args:
            item_id: STAC Item ID to check
            
        Returns:
            True if item_id exists in checkpoint state (O(1) lookup)
        """
        return item_id in self._processed_items
    
    def _load_checkpoint_state(self) -> None:
        """Load checkpoint state from Parquet files."""
        # For now, just initialize empty set
        # Will implement Parquet loading in next task
        self._processed_items = set()
