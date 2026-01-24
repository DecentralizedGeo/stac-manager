"""Transform Module - Sidecar data enrichment."""
import json
from pathlib import Path
from stac_manager.modules.config import TransformConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import ConfigurationError
from stac_manager.utils import apply_jmespath, deep_merge


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
            
            # Build index
            if isinstance(self.sidecar_data, dict):
                # Dict: keys are IDs
                self.sidecar_index = self.sidecar_data
            elif isinstance(self.sidecar_data, list):
                # List: extract IDs using jmespath
                for entry in self.sidecar_data:
                    item_id = apply_jmespath(entry, self.config.sidecar_id_path)
                    if item_id:
                        self.sidecar_index[str(item_id)] = entry
            else:
                raise ConfigurationError("input_file must be JSON dict or list")

    def modify(self, item: dict, context: WorkflowContext) -> dict:
        """
        Enrich STAC item with sidecar data.
        
        Args:
            item: STAC item dict
            context: Workflow context
            
        Returns:
            Enriched item dict
        """
        item_id = item.get("id")
        if not item_id or item_id not in self.sidecar_index:
            if self.config.handle_missing == 'warn':
                context.failure_collector.add(
                    item_id=item_id or "unknown",
                    error=f"Missing sidecar data for item ID: {item_id}",
                    step_id="transform"
                )
            elif self.config.handle_missing == 'error':
                from stac_manager.exceptions import DataProcessingError
                raise DataProcessingError(f"Missing sidecar data for item ID: {item_id}")
            return item
            
        sidecar_entry = self.sidecar_index[item_id]
        
        # Apply field mapping if provided
        if self.config.field_mapping:
            sidecar_data = {}
            for target_field, source_query in self.config.field_mapping.items():
                val = apply_jmespath(sidecar_entry, source_query)
                sidecar_data[target_field] = val
        else:
            sidecar_data = sidecar_entry
        
        # Determine merge strategy
        # Transform 'merge' -> deep_merge 'keep_existing'
        # Transform 'update' -> deep_merge 'overwrite'
        merge_strategy = 'keep_existing' if self.config.strategy == 'merge' else 'overwrite'
        
        # Sidecar data is merged into item['properties'] by default
        target = item.get("properties", {})
        
        item["properties"] = deep_merge(
            target,
            sidecar_data,
            strategy=merge_strategy
        )
        
        return item
