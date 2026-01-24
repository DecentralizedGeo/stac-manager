"""Ingest Module - Fetch STAC Items from files or APIs."""
import json
import asyncio
from pathlib import Path
from typing import AsyncIterator

from stac_manager.modules.config import IngestConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import ConfigurationError


class IngestModule:
    """Fetches STAC Items from local files or remote APIs."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with configuration."""
        self.config = IngestConfig(**config)
        
        # Validate file exists for file mode
        if self.config.mode == "file":
            source_path = Path(self.config.source)
            if not source_path.exists():
                raise ConfigurationError(f"File not found: {self.config.source}")
    
    async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
        """
        Fetch items from configured source.
        
        Args:
            context: Workflow context
        
        Yields:
            STAC item dicts
        """
        if self.config.mode == "file":
            async for item in self._fetch_from_file():
                yield item
        else:
            async for item in self._fetch_from_api(context):
                yield item
    
    async def _fetch_from_file(self) -> AsyncIterator[dict]:
        """Fetch items from local file."""
        if self.config.format == "json":
            # Read JSON file
            source_path = Path(self.config.source)
            content = await asyncio.to_thread(source_path.read_text)
            items = json.loads(content)
            
            # Handle both FeatureCollection and list formats
            if isinstance(items, dict) and items.get("type") == "FeatureCollection":
                items = items.get("features", [])
            
            for item in items:
                yield item
        elif self.config.format == "parquet":
            # Parquet handling (Task 37)
            raise NotImplementedError("Parquet ingestion not yet implemented")
    
    async def _fetch_from_api(self, context: WorkflowContext) -> AsyncIterator[dict]:
        """Fetch items from STAC API."""
        # API mode implementation (Task 38)
        raise NotImplementedError("API ingestion not yet implemented")
