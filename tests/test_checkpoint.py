from stac_manager.checkpoint import CheckpointManager
import tempfile
import pandas as pd
import os

def test_checkpoint_save_and_check():
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = CheckpointManager(tmpdir, "wf-1", "step-1")
        cm.save([{"item_id": "item1", "step_id": "step-1", "timestamp": "...", "status": "success"}])
        
        assert cm.contains("item1")
        assert not cm.contains("item2")
