"""Tests for checkpoint management."""
import pytest
from pathlib import Path
import tempfile
import shutil
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
