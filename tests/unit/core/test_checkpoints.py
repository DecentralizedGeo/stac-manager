"""Tests for checkpoint management."""
import pytest
from pathlib import Path
import tempfile
from datetime import datetime, timezone
import pandas as pd
from stac_manager.core.checkpoints import CheckpointManager, CheckpointRecord


def test_checkpoint_manager_initialization():
    """Test CheckpointManager creates directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        workflow_id = "test-workflow"
        step_id = "ingest"
        
        manager = CheckpointManager(
            directory=base_dir,
            workflow_id=workflow_id,
            step_id=step_id
        )
        
        # Verify checkpoint path
        expected_path = base_dir / workflow_id / step_id
        assert manager.get_checkpoint_path() == expected_path
        
        # Verify directory created
        assert expected_path.exists()
        assert expected_path.is_dir()


def test_checkpoint_manager_empty_state():
    """Test CheckpointManager with no existing checkpoints."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CheckpointManager(
            directory=Path(tmpdir),
            workflow_id="test-workflow",
            step_id="step1"
        )
        
        # Should not contain any items
        assert not manager.contains("item-1")
        assert not manager.contains("item-2")


def test_checkpoint_record_structure():
    """Test CheckpointRecord TypedDict structure."""
    record = CheckpointRecord(
        item_id="test-item-1",
        step_id="ingest",
        timestamp="2026-01-24T12:00:00Z",
        status="success"
    )
    
    assert record["item_id"] == "test-item-1"
    assert record["step_id"] == "ingest"
    assert record["timestamp"] == "2026-01-24T12:00:00Z"
    assert record["status"] == "success"


def test_checkpoint_save_single_record():
    """Test saving a single checkpoint record."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CheckpointManager(
            directory=Path(tmpdir),
            workflow_id="test-workflow",
            step_id="step1"
        )
        
        # Save record
        records = [
            CheckpointRecord(
                item_id="item-1",
                step_id="step1",
                timestamp=datetime.now(timezone.utc).isoformat(),
                status="success"
            )
        ]
        
        manager.save(records)
        
        # Verify item is now tracked
        assert manager.contains("item-1")
        assert not manager.contains("item-2")


def test_checkpoint_save_multiple_records():
    """Test saving multiple checkpoint records."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CheckpointManager(
            directory=Path(tmpdir),
            workflow_id="test-workflow",
            step_id="step1"
        )
        
        # Save batch
        records = [
            CheckpointRecord(
                item_id=f"item-{i}",
                step_id="step1",
                timestamp=datetime.now(timezone.utc).isoformat(),
                status="success"
            )
            for i in range(5)
        ]
        
        manager.save(records)
        
        # Verify all items tracked
        for i in range(5):
            assert manager.contains(f"item-{i}")


def test_checkpoint_save_creates_parquet_file():
    """Test that save creates a Parquet file on disk."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CheckpointManager(
            directory=Path(tmpdir),
            workflow_id="test-workflow",
            step_id="step1"
        )
        
        records = [
            CheckpointRecord(
                item_id="item-1",
                step_id="step1",
                timestamp="2026-01-24T12:00:00Z",
                status="success"
            )
        ]
        
        manager.save(records)
        
        # Verify parquet file exists
        checkpoint_path = manager.get_checkpoint_path()
        parquet_files = list(checkpoint_path.glob("*.parquet"))
        
        assert len(parquet_files) >= 1
        
        # Verify file contents
        df = pd.read_parquet(parquet_files[0])
        assert len(df) == 1
        assert df.iloc[0]["item_id"] == "item-1"
        assert df.iloc[0]["status"] == "success"
