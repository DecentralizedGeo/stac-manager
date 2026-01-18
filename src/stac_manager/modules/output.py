from typing import Literal, List, TypedDict, Any
from pydantic import BaseModel
import os
import json
from stac_manager.context import WorkflowContext

class OutputConfig(BaseModel):
    format: Literal['json', 'parquet']
    output_path: str
    organize_by: Literal['item_id', 'flat'] = 'item_id'

class OutputResult(TypedDict):
    files_written: List[str]
    manifest_path: str
    manifest: dict
    
class OutputModule:
    """Writes items to disk."""
    
    def __init__(self, config: dict):
        self.config = OutputConfig(**config)
        self._buffer: List[dict] = []
        self._files_written: List[str] = []
        
        # Create dir
        os.makedirs(self.config.output_path, exist_ok=True)
        
    async def bundle(self, item: dict, context: WorkflowContext) -> None:
        if self.config.format == 'json':
            self._write_json_item(item)
        else:
            self._buffer.append(item)
            # Flush if buffer full (simple logic for now)

    def _write_json_item(self, item: dict):
        filename = f"{item.get('id', 'unknown')}.json"
        path = os.path.join(self.config.output_path, filename)
        with open(path, "w") as f:
            json.dump(item, f)
        self._files_written.append(path)

    async def finalize(self, context: WorkflowContext) -> OutputResult:
        # Flush remaining buffer (parquet)
        if self.config.format == 'parquet' and self._buffer:
            # Placeholder for parquet writing using stac-geoparquet or pandas
             pass
            
        manifest_path = os.path.join(self.config.output_path, "manifest.json")
        manifest = {
            "files": self._files_written,
            "total": len(self._files_written)
        }
        with open(manifest_path, "w") as f:
            json.dump(manifest, f)
            
        return {
            "files_written": self._files_written,
            "manifest_path": manifest_path,
            "manifest": manifest
        }
