from typing import Any
import json
import logging
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
        self.logger = logging.getLogger(__name__)  # Default logger
        
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

    def set_logger(self, logger: logging.Logger) -> None:
        """Set step-specific logger for this module.
        
        Args:
            logger: Logger instance to use for this module
        """
        self.logger = logger

    
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
        item_id = item.get('id', 'unknown')
        changes = []  # Track changes for summary logging
        
        self.logger.debug(f"Processing item | item: {item_id}")

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
                        path_str = '.'.join(path_tuple)
                        self.logger.debug(
                            f"Removed field | item: {item_id} | path: {path_str}"
                        )
                        changes.append(f"remove {path_str}")
            
            # Log INFO summary if fields were removed
            if expanded_paths:
                self.logger.info(
                    f"Removed fields | item: {item_id} | count: {len(expanded_paths)} | "
                    f"patterns: {self.config.removes}"
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
            
            # Apply each expanded update
            for field_path, value in expanded_updates.items():
                # Log detailed change at DEBUG level
                self.logger.debug(
                    f"Set field | item: {item_id} | path: {field_path} | value: {value}"
                )
                
                set_nested_field(
                    item,
                    field_path,
                    value,
                    create_missing=self.config.create_missing_paths
                )
                changes.append(f"set {field_path}")

        # 3. Apply item-specific patches
        if self.patches:
            item_id = item.get("id")
            if item_id and item_id in self.patches:
                patch_data = self.patches[item_id]
                
                self.logger.debug(
                    f"Applying patch | item: {item_id} | mode: {self.config.mode}"
                )
                
                if self.config.mode == 'replace':
                    item = patch_data
                    changes.append("apply patch (replace)")
                else:  # merge or update_only
                    strategy = 'update_only' if self.config.mode == 'update_only' else 'overwrite'
                    item = deep_merge(item, patch_data, strategy=strategy)
                    changes.append(f"apply patch ({strategy})")
                
                self.logger.info(
                    f"Applied patch | item: {item_id} | mode: {self.config.mode}"
                )

        # 4. Auto-update timestamp
        if self.config.auto_update_timestamp:
            now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            set_nested_field(
                item,
                "properties.updated",
                now,
                create_missing=True
            )
            self.logger.debug(
                f"Updated timestamp | item: {item_id} | timestamp: {now}"
            )
            changes.append("update timestamp")
        
        # Summary log at INFO level
        if changes:
            self.logger.info(
                f"Applied updates | item: {item_id} | changes: {len(changes)}"
            )
        
        return item
