"""Checkpoint management for workflow state persistence."""
from pathlib import Path
from typing import TypedDict, Optional
from datetime import datetime, timezone
import shutil
import tempfile
import os
import pandas as pd


class CheckpointRecord(TypedDict):
    """Single checkpoint record tracking item completion through pipeline."""
    item_id: str
    collection_id: str
    output_path: str
    completed: bool
    timestamp: str  # ISO 8601
    error: Optional[str]  # Error message if failed


class CheckpointManager:
    """
    Manages pipeline completion tracking using a single Parquet file per collection.

    Tracks which items have successfully completed the entire pipeline
    (reached OutputModule and were written to disk). This enables:
    - Resume workflows from interruptions
    - Skip already-completed items when re-running
    - Retry only failed items
    
    Directory structure: {checkpoint_root}/{workflow_id}/{collection_id}.parquet
    
    Design Philosophy:
        Checkpoint = "Did this item complete the full pipeline?"
        NOT "Did this item pass through step X?"
        
        This means we check completion status AFTER the entire pipeline,
        allowing us to skip HTTP requests for items already successfully processed.
    """

    def __init__(
        self,
        workflow_id: str,
        collection_id: str,
        checkpoint_root: Path | str = "./checkpoints",
        buffer_size: int = 1000,
        resume_from_existing: bool = True
    ):
        """
        Initialize checkpoint manager for a specific collection in a workflow.

        Args:
            workflow_id: Unique workflow identifier
            collection_id: Collection ID being processed (e.g., 'HLSS30')
            checkpoint_root: Root directory for all checkpoints
            buffer_size: Number of records to buffer before flushing to disk
            resume_from_existing: If False, ignore existing checkpoints and start fresh
        """
        self.workflow_id = workflow_id
        self.collection_id = collection_id
        self.checkpoint_root = Path(checkpoint_root)
        self.buffer_size = buffer_size

        # Build checkpoint file path: {root}/{workflow}/{collection}.parquet
        checkpoint_dir = self.checkpoint_root / self.workflow_id
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._checkpoint_file = checkpoint_dir / f"{self.collection_id}.parquet"

        # Internal buffer for records
        self._buffer: list[CheckpointRecord] = []

        # Load existing state - track completed items only
        self._completed_items: set[str] = set()
        if resume_from_existing:
            self._load_checkpoint_state()

    def get_checkpoint_path(self) -> Path:
        """Return full path to checkpoint file."""
        return self._checkpoint_file

    def is_completed(self, item_id: str) -> bool:
        """
        Check if an item has successfully completed the entire pipeline.

        Args:
            item_id: STAC Item ID to check

        Returns:
            True if item_id successfully completed pipeline (O(1) lookup)
        """
        return item_id in self._completed_items

    def mark_completed(self, item_id: str, output_path: str) -> None:
        """
        Mark an item as successfully completed through the pipeline.
        
        Call this after OutputModule successfully writes the item to disk.
        Automatically flushes to disk when buffer reaches buffer_size.

        Args:
            item_id: STAC Item ID that completed
            output_path: Path where the item was written
        """
        record: CheckpointRecord = {
            "item_id": item_id,
            "collection_id": self.collection_id,
            "output_path": output_path,
            "completed": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": None
        }
        self._buffer.append(record)
        self._completed_items.add(item_id)
        
        # Auto-flush when buffer is full
        if len(self._buffer) >= self.buffer_size:
            self.flush()

    def mark_failed(self, item_id: str, error: str) -> None:
        """
        Mark an item as failed during pipeline processing.
        
        Failed items will be retried on next workflow run.
        Automatically flushes to disk when buffer reaches buffer_size.

        Args:
            item_id: STAC Item ID that failed
            error: Error message describing the failure
        """
        record: CheckpointRecord = {
            "item_id": item_id,
            "collection_id": self.collection_id,
            "output_path": "",
            "completed": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": error
        }
        self._buffer.append(record)
        # Note: Do NOT add to _completed_items, so it will be retried
        
        # Auto-flush when buffer is full
        if len(self._buffer) >= self.buffer_size:
            self.flush()

    def contains(self, item_id: str) -> bool:
        """
        DEPRECATED: Use is_completed() instead.
        
        Check if an item has already been processed.

        Args:
            item_id: STAC Item ID to check

        Returns:
            True if item_id exists in checkpoint state (O(1) lookup)
        """
        return self.is_completed(item_id)

    def add(self, record: CheckpointRecord) -> None:
        """
        DEPRECATED: Use mark_completed() or mark_failed() instead.
        
        Add a single checkpoint record to the buffer.
        
        Automatically flushes to disk when buffer reaches buffer_size.

        Args:
            record: CheckpointRecord to add
        """
        self._buffer.append(record)
        if record["completed"]:
            self._completed_items.add(record["item_id"])
        
        # Auto-flush when buffer is full
        if len(self._buffer) >= self.buffer_size:
            self.flush()

    def save(self, new_records: list[CheckpointRecord]) -> None:
        """
        DEPRECATED: Use mark_completed() or mark_failed() instead.
        
        Add multiple checkpoint records to the buffer.
        
        Automatically flushes to disk when buffer reaches buffer_size.

        Args:
            new_records: List of CheckpointRecord dicts to add
        """
        for record in new_records:
            self._buffer.append(record)
            if record["completed"]:
                self._completed_items.add(record["item_id"])
        
        # Auto-flush if buffer exceeds threshold
        if len(self._buffer) >= self.buffer_size:
            self.flush()

    def flush(self) -> None:
        """
        Flush buffered records to checkpoint file atomically.
        
        Strategy:
            1. Load existing checkpoint file (if exists)
            2. Append buffered records
            3. Write to temporary file
            4. Atomic rename to final checkpoint file
            
        This ensures the checkpoint file is never corrupted and always
        contains the complete history of all items (completed and failed).
        """
        if not self._buffer:
            return

        # Load existing checkpoint data
        existing_df = None
        if self._checkpoint_file.exists():
            existing_df = pd.read_parquet(self._checkpoint_file)

        # Create new records dataframe
        new_df = pd.DataFrame(self._buffer)

        # Concatenate with existing data
        if existing_df is not None and not existing_df.empty:
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined_df = new_df

        # Write to temp file atomically (same pattern as Singularity script)
        fd, temp_path = tempfile.mkstemp(
            suffix=".parquet",
            dir=self._checkpoint_file.parent
        )
        
        try:
            os.close(fd)
            combined_df.to_parquet(temp_path, index=False)
            # Atomic rename (on same filesystem)
            shutil.move(temp_path, self._checkpoint_file)
        except Exception:
            # Clean up temp file if something went wrong
            if Path(temp_path).exists():
                Path(temp_path).unlink()
            raise

        # Clear buffer after successful write
        self._buffer.clear()

    def __del__(self) -> None:
        """Flush any remaining buffered records on cleanup."""
        try:
            self.flush()
        except Exception:
            # Silently ignore errors during cleanup
            pass

    def _load_checkpoint_state(self) -> None:
        """Load checkpoint state from checkpoint file."""
        if not self._checkpoint_file.exists():
            return

        # Read checkpoint file
        df = pd.read_parquet(self._checkpoint_file)

        # Build set of COMPLETED item IDs only (deduplicate)
        # Failed items are not added, so they will be retried
        completed_df = df[df["completed"]]
        self._completed_items = set(completed_df["item_id"].unique())
