from typing import Any
import json
from pathlib import Path
from stac_manager.modules.config import UpdateConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.utils.field_ops import deep_merge, expand_wildcard_paths, expand_wildcard_removal_paths, set_nested_field
from stac_manager.exceptions import ConfigurationError
from datetime import datetime, timezone


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
            context: Workflow context (used for wildcard expansion context values)
            
        Returns:
            Modified item dict
        """
        context.logger.debug(f"Modifying item {item.get('id', 'unknown')}")

        # 1. Apply strict removals (Global) - with wildcard expansion
        if self.config.removes:
            # Expand wildcards to get all matching paths
            expanded_paths = expand_wildcard_removal_paths(
                self.config.removes,
                item
            )
            
            # Remove each expanded path
            for path_tuple in expanded_paths:
                # Navigate to parent and remove the final key
                target = item
                for key in path_tuple[:-1]:
                    if key in target and isinstance(target[key], dict):
                        target = target[key]
                    else:
                        break
                else:
                    if path_tuple[-1] in target:
                        del target[path_tuple[-1]]
                        context.logger.debug(
                            f"Removed field {'.'.join(path_tuple)} from {item.get('id')}"
                        )
        
        # 2. Apply global field updates (with wildcard expansion)
        if self.config.updates:
            # Expand wildcards to actual paths in this item
            expanded_updates = expand_wildcard_paths(
                self.config.updates,
                item,
                context={
                    "item_id": item.get("id"),
                    "collection_id": item.get("collection")
                }
            )
            
            if expanded_updates:
                context.logger.debug(f"Applying updates to fields {list(expanded_updates.keys())} for {item.get('id')}")
            
            # Apply each expanded update
            for field_path, value in expanded_updates.items():
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
                context.logger.debug(f"Applying patch to {item_id}")
                
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
