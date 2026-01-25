"""Checkpoint management for workflow state persistence."""
from pathlib import Path
from typing import TypedDict
from datetime import datetime, timezone
import uuid
import pandas as pd


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
    
    def save(self, new_records: list[CheckpointRecord]) -> None:
        """
        Atomically append new records to checkpoint using partitioned writes.
        
        Args:
            new_records: List of CheckpointRecord dicts to persist
            
        Implementation:
            1. Generate unique filename: checkpoint_{timestamp}_{uuid}.parquet
            2. Write records to temporary file: .tmp/{filename}
            3. Move temp file to checkpoint directory atomically
            4. Update in-memory processed set with new item_ids
        """
        if not new_records:
            return
        
        # Generate unique filename
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"checkpoint_{timestamp}_{unique_id}.parquet"
        
        # Create temp directory
        temp_dir = self._checkpoint_path / ".tmp"
        temp_dir.mkdir(exist_ok=True)
        
        temp_path = temp_dir / filename
        final_path = self._checkpoint_path / filename
        
        # Write to temporary file
        df = pd.DataFrame(new_records)
        df.to_parquet(temp_path, index=False)
        
        # Atomic rename
        temp_path.rename(final_path)
        
        # Update in-memory set
        for record in new_records:
            self._processed_items.add(record["item_id"])
    
    def _load_checkpoint_state(self) -> None:
        """Load checkpoint state from Parquet files."""
        # Find all parquet files (exclude .tmp directory)
        parquet_files = [
            f for f in self._checkpoint_path.glob("*.parquet")
            if f.is_file()
        ]
        
        if not parquet_files:
            return
        
        # Read and concatenate all checkpoint files
        dfs = [pd.read_parquet(f) for f in parquet_files]
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Build set of processed item IDs (deduplicate)
        self._processed_items = set(combined_df["item_id"].unique())
