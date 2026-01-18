from pathlib import Path
from typing import TypedDict, List
import pandas as pd
import uuid

class CheckpointRecord(TypedDict):
    item_id: str
    step_id: str
    timestamp: str
    status: str

class CheckpointManager:
    def __init__(self, directory: str, workflow_id: str, step_id: str):
        self.base_path = Path(directory) / workflow_id / step_id
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._cache = set()
        self._load_state()
        
    def _load_state(self):
        # Load all parquet files in dir
        for f in self.base_path.glob("*.parquet"):
            try:
                df = pd.read_parquet(f)
                if 'item_id' in df.columns:
                    self._cache.update(df['item_id'].tolist())
            except Exception:
                # Log warning in real code
                pass
            
    def contains(self, item_id: str) -> bool:
        return item_id in self._cache
        
    def save(self, new_records: List[CheckpointRecord]):
        if not new_records:
            return
            
        df = pd.DataFrame(new_records)
        fname = f"checkpoint_{uuid.uuid4()}.parquet"
        
        # Atomic write simulation
        # Using pyarrow engine by default if installed
        df.to_parquet(self.base_path / fname)
        self._cache.update([r['item_id'] for r in new_records])
