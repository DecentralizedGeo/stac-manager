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
            # Read Parquet file
            import pyarrow.parquet as pq
            
            source_path = Path(self.config.source)
            # Use thread pool for blocking I/O
            table = await asyncio.to_thread(pq.read_table, str(source_path))
            
            # Convert to dicts and yield
            items = table.to_pylist()
            for item in items:
                yield item
    
    async def _fetch_from_api(self, context: WorkflowContext) -> AsyncIterator[dict]:
        """Fetch items from STAC API."""
        import pystac_client
        
        # Open STAC API client
        client = pystac_client.Client.open(self.config.source)
        
        # Build search parameters
        search_params = {
            "limit": self.config.limit,
        }
        
        if self.config.collections:
            search_params["collections"] = self.config.collections
        
        if self.config.max_items:
            search_params["max_items"] = self.config.max_items
        
        # Execute search
        search = client.search(**search_params)
        
        # items_as_dicts() is a regular iterator, not async
        # Wrap in async iterator for consistency
        for item in search.items_as_dicts():
            yield item
