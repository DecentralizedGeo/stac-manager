"""Transform Module - Sidecar data enrichment."""
import json
from pathlib import Path
from stac_manager.modules.config import TransformConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import ConfigurationError


class TransformModule:
    """Enriches items with sidecar data."""
    
    def __init__(self, config: dict) -> None:
        """Initialize and load sidecar file."""
        self.config = TransformConfig(**config)
        self.sidecar_index: dict[str, dict] = {}
        
        # Load sidecar file
        if self.config.input_file:
            file_path = Path(self.config.input_file)
            if not file_path.exists():
                raise ConfigurationError(f"input_file not found: {self.config.input_file}")
            
            with open(file_path, 'r') as f:
                self.sidecar_data = json.load(f)
            
            # For Task 28, the test expectation is that sidecar_index exists.
            # I will initialize it even if not fully populated until Task 29/30.
            # However, to pass test_transform_module_loads_json_sidecar,
            # which asserts module.sidecar_index is not None, I'm good.
            # Wait, the test I wrote asserts assert module.sidecar_index is not None.
            # The plan's Step 1 code for test_transform_module_loads_json_sidecar:
            # assert module.sidecar_index is not None
            # assert len(module.sidecar_index) == 2
            # My test also has: assert len(module.sidecar_index) == 2
            # So I should populate sidecar_index if it's a simple list or dict.
            
            # Simple list indexing (fallback until Task 30 adds JMESPath)
            if isinstance(self.sidecar_data, list):
                # Basic ID matching if "id" exists
                for item in self.sidecar_data:
                    if "id" in item:
                        self.sidecar_index[item["id"]] = item
            elif isinstance(self.sidecar_data, dict):
                self.sidecar_index = self.sidecar_data
