import json
from pathlib import Path
from stac_manager.modules.config import UpdateConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.utils.field_ops import set_nested_field, deep_merge
from datetime import datetime, timezone


class UpdateModule:
    """Modifies existing STAC Items."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with configuration."""
        self.config = UpdateConfig(**config)
    
    def modify(self, item: dict, context: WorkflowContext) -> dict | None:
        """
        Apply updates to item.
        
        Args:
            item: STAC item dict
            context: Workflow context
            
        Returns:
            Modified item dict
        """
        # Apply patch file
        if self.config.patch_file:
            path = Path(self.config.patch_file)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    patch_data = json.load(f)
                    
                if self.config.mode == 'replace':
                    item = patch_data
                else:  # merge
                    item = deep_merge(item, patch_data, strategy='overwrite')
            else:
                context.failure_collector.add(
                    item_id=item.get("id", "unknown"),
                    error=f"Patch file not found: {path}",
                    step_id="update"
                )

        # Apply field updates
        if self.config.updates:
            for field_path, value in self.config.updates.items():
                set_nested_field(
                    item,
                    field_path,
                    value
                )
        
        # Apply strict removals
        if self.config.removes:
            for field_path in self.config.removes:
                # Handle nested removal if needed, for now simple top-level or use utility
                # For this task, we'll implement simple recursive removal
                parts = field_path.split('.')
                target = item
                for part in parts[:-1]:
                    if part in target:
                        target = target[part]
                    else:
                        break
                else:
                    if parts[-1] in target:
                        del target[parts[-1]]
        
        # Auto-update timestamp
        if self.config.auto_update_timestamp:
            now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            set_nested_field(item, "properties.updated", now)
        
        return item
