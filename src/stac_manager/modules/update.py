from typing import Any
import json
from pathlib import Path
from stac_manager.modules.config import UpdateConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.utils.field_ops import deep_merge
from stac_manager.exceptions import ConfigurationError, DataProcessingError
from datetime import datetime, timezone


def set_field_with_path_creation(item: dict, path: str, value: Any, create_paths: bool) -> None:
    """
    Set nested field with optional path creation and error handling.
    """
    keys = path.split('.')
    current = item
    
    for i, key in enumerate(keys[:-1]):
        if key not in current:
            if not create_paths:
                raise DataProcessingError(f"Path does not exist: {'.'.join(keys[:i+1])}")
            current[key] = {}
        
        if not isinstance(current[key], dict):
            raise DataProcessingError(f"Cannot traverse non-dict at: {'.'.join(keys[:i+1])}")
        
        current = current[key]
    
    current[keys[-1]] = value


class UpdateModule:
    """Modifies existing STAC Items."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with configuration."""
        self.config = UpdateConfig(**config)
        self.patches: dict[str, dict] = {}
        
        # Load patch file once during initialization
        if self.config.patch_file:
            path = Path(self.config.patch_file)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    self.patches = json.load(f)
            else:
                # We can't use failure_collector here contextually, so we might want to log or raise 
                # strictly if file is missing at startup (Tier 1).
                # But to maintain current behavior (runtime error collection), we'll skip loading
                # and let modify handle the missing file error? 
                # NOTE: Init shouldn't take context. So we raise ConfigurationError.
                raise ConfigurationError(f"Patch file not found: {path}")

    
    def modify(self, item: dict, context: WorkflowContext) -> dict | None:
        """
        Apply updates to item.
        
        Note: Patches are applied after global updates and removals to allow specific overrides.

        Args:
            item: STAC item dict
            context: Workflow context
            
        Returns:
            Modified item dict
        """
        # 1. Apply strict removals (Global)
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
        
        # 2. Apply global field updates
        if self.config.updates:
            for field_path, value in self.config.updates.items():
                set_field_with_path_creation(
                    item,
                    field_path,
                    value,
                    create_paths=self.config.create_missing_paths
                )

        # 3. Apply item-specific patches
        if self.patches:
            item_id = item.get("id")
            if item_id and item_id in self.patches:
                patch_data = self.patches[item_id]
                
                if self.config.mode == 'replace':
                    item = patch_data
                else:  # merge or update_only
                    strategy = 'update_only' if self.config.mode == 'update_only' else 'overwrite'
                    item = deep_merge(item, patch_data, strategy=strategy)

        # 4. Auto-update timestamp
        if self.config.auto_update_timestamp:
            now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            set_field_with_path_creation(
                item,
                "properties.updated",
                now,
                create_paths=True
            )
        
        return item
