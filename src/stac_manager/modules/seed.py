"""Seed Module - Generator source for skeleton items."""
from typing import AsyncIterator
from stac_manager.modules.config import SeedConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.utils.field_ops import deep_merge


class SeedModule:
    """Yields skeleton STAC Items from configured list."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with configuration."""
        self.config = SeedConfig(**config)
    
    async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
        """
        Yields items from config or source file.
        
        Args:
            context: Workflow context
        
        Yields:
            STAC item dicts
        """
        items_list = self.config.items or []
        
        for item_entry in items_list:
            item_dict = {}
            
            # Normalize to dict
            if isinstance(item_entry, str):
                item_dict = {"id": item_entry}
            elif isinstance(item_entry, dict):
                item_dict = item_entry.copy()
            else:
                raise ValueError(f"Invalid item format: {type(item_entry)}")
            
            # Apply defaults (defaults as base, item overrides)
            if self.config.defaults:
                final_item = self.config.defaults.copy()
                final_item = deep_merge(final_item, item_dict, strategy='overwrite')
                item_dict = final_item
            
            yield item_dict

