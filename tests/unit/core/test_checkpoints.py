"""Tests for checkpoint management."""
import pytest
from pathlib import Path
import tempfile
import pandas as pd
from stac_manager.core.checkpoints import CheckpointManager, CheckpointRecord


def test_checkpoint_manager_initialization():
    """Test CheckpointManager creates directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        workflow_id = "test-workflow"
        collection_id = "test-collection"

        manager = CheckpointManager(
            workflow_id=workflow_id,
            collection_id=collection_id,
            checkpoint_root=base_dir
        )

        # Verify checkpoint file path
        expected_file = base_dir / workflow_id / f"{collection_id}.parquet"
        assert manager.get_checkpoint_path() == expected_file

        # Verify directory created
        assert expected_file.parent.exists()
        assert expected_file.parent.is_dir()


def test_checkpoint_manager_empty_state():
    """Test CheckpointManager with no existing checkpoints."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CheckpointManager(
            workflow_id="test-workflow",
            collection_id="test-collection",
            checkpoint_root=Path(tmpdir)
        )

        # Should not contain any items
        assert not manager.is_completed("item-1")
        assert not manager.is_completed("item-2")


def test_checkpoint_record_structure():
    """Test CheckpointRecord TypedDict structure."""
    record = CheckpointRecord(
        item_id="test-item-1",
        collection_id="test-collection",
        output_path="/output/item-1.json",
        completed=True,
        timestamp="2026-01-24T12:00:00Z",
        error=None
    )

    assert record["item_id"] == "test-item-1"
    assert record["collection_id"] == "test-collection"
    assert record["output_path"] == "/output/item-1.json"
    assert record["completed"] is True
    assert record["timestamp"] == "2026-01-24T12:00:00Z"
    assert record["error"] is None


def test_checkpoint_save_single_record():
    """Test marking a single item as completed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CheckpointManager(
            workflow_id="test-workflow",
            collection_id="test-collection",
            checkpoint_root=Path(tmpdir)
        )

        # Mark item as completed
        manager.mark_completed("item-1", "/output/item-1.json")
        manager.flush()

        # Verify item is now tracked as completed
        assert manager.is_completed("item-1")
        assert not manager.is_completed("item-2")


def test_checkpoint_save_multiple_records():
    """Test marking multiple items as completed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CheckpointManager(
            workflow_id="test-workflow",
            collection_id="test-collection",
            checkpoint_root=Path(tmpdir)
        )

        # Mark multiple items as completed
        for i in range(5):
            manager.mark_completed(f"item-{i}", f"/output/item-{i}.json")

        manager.flush()

        # Verify all items tracked as completed
        for i in range(5):
            assert manager.is_completed(f"item-{i}")


def test_checkpoint_save_creates_parquet_file():
    """Test that marking items as completed creates a Parquet file on disk."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CheckpointManager(
            workflow_id="test-workflow",
            collection_id="test-collection",
            checkpoint_root=Path(tmpdir)
        )

        manager.mark_completed("item-1", "/output/item-1.json")
        manager.flush()

        # Verify parquet file exists
        checkpoint_file = manager.get_checkpoint_path()
        assert checkpoint_file.exists()

        # Verify file contents
        df = pd.read_parquet(checkpoint_file)
        assert len(df) == 1
        assert df.iloc[0]["item_id"] == "item-1"
        assert df.iloc[0]["completed"]  # pandas returns numpy bool, check truthiness
        assert df.iloc[0]["output_path"] == "/output/item-1.json"


def test_checkpoint_resume_from_existing_state():
    """Test CheckpointManager loads existing checkpoints on initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_dir = Path(tmpdir)
        workflow_id = "resume-workflow"
        collection_id = "test-collection"

        # First manager: Mark some items as completed
        manager1 = CheckpointManager(
            workflow_id=workflow_id,
            collection_id=collection_id,
            checkpoint_root=checkpoint_dir
        )

        for i in range(10):
            manager1.mark_completed(f"item-{i}", f"/output/item-{i}.json")

        manager1.flush()

        # Verify first manager knows about items
        assert manager1.is_completed("item-5")

        # Second manager: Should load existing state
        manager2 = CheckpointManager(
            workflow_id=workflow_id,
            collection_id=collection_id,
            checkpoint_root=checkpoint_dir
        )

        # Should contain all previously completed items
        for i in range(10):
            assert manager2.is_completed(f"item-{i}")

        # Should not contain items not yet completed
        assert not manager2.is_completed("item-99")


def test_checkpoint_resume_with_multiple_partitions():
    """Test CheckpointManager handles multiple flush operations correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CheckpointManager(
            workflow_id="multi-partition",
            collection_id="test-collection",
            checkpoint_root=Path(tmpdir)
        )

        # Mark items in multiple batches
        for batch_num in range(3):
            for i in range(5):
                manager.mark_completed(
                    f"batch{batch_num}-item-{i}",
                    f"/output/batch{batch_num}-item-{i}.json"
                )
            manager.flush()

        # New manager should load all previously completed items
        manager_new = CheckpointManager(
            workflow_id="multi-partition",
            collection_id="test-collection",
            checkpoint_root=Path(tmpdir)
        )

        # Verify all items from all batches
        for batch_num in range(3):
            for i in range(5):
                assert manager_new.is_completed(f"batch{batch_num}-item-{i}")


def test_checkpoint_handles_duplicate_items():
    """Test CheckpointManager handles duplicate item IDs correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CheckpointManager(
            workflow_id="dedup-test",
            collection_id="test-collection",
            checkpoint_root=Path(tmpdir)
        )

        # Mark same item multiple times (simulating retries)
        for _ in range(3):
            manager.mark_completed("duplicate-item", "/output/duplicate-item.json")
            manager.flush()

        # Should still be tracked as completed (idempotent)
        assert manager.is_completed("duplicate-item")

        # Reload and verify still tracked
        manager_new = CheckpointManager(
            workflow_id="dedup-test",
            collection_id="test-collection",
            checkpoint_root=Path(tmpdir)
        )

        assert manager_new.is_completed("duplicate-item")
