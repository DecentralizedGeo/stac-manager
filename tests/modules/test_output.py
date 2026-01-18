from stac_manager.modules.output import OutputModule
from stac_manager.context import WorkflowContext
from unittest.mock import MagicMock
import os
import json
import pytest

@pytest.mark.asyncio

@pytest.mark.asyncio
async def test_output_json_writer(tmp_path):
    config = {
        "format": "json",
        "output_path": str(tmp_path),
        "organize_by": "flat"
    }
    module = OutputModule(config)
    ctx = MagicMock(spec=WorkflowContext)
    
    item = {"id": "item1", "type": "Feature", "properties": {}}
    await module.bundle(item, ctx)
    result = await module.finalize(ctx)
    
    assert os.path.exists(tmp_path / "item1.json")
    with open(tmp_path / "item1.json") as f:
        data = json.load(f)
        assert data['id'] == "item1"
