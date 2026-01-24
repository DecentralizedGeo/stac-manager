"""Ingest Module - Fetch STAC Items from files or APIs.

This module provides the IngestModule class for loading STAC items from various sources
including local JSON/Parquet files and remote STAC API endpoints.

Example:
    Basic file ingestion::

        from stac_manager.modules.ingest import IngestModule
        from stac_manager.core.context import WorkflowContext
        
        # Load from JSON file
        config = {
            "mode": "file",
            "source": "items.json",
            "format": "json"
        }
        ingest = IngestModule(config)
        
        context = WorkflowContext.create()
        async for item in ingest.fetch(context):
            print(f"Loaded item: {item['id']}")
    
    API ingestion with filters::

        # Load from STAC API
        config = {
            "mode": "api",
            "source": "https://earth-search.aws.element84.com/v1",
            "collection_id": "sentinel-2-l2a",
            "bbox": [-122.5, 37.5, -122.0, 38.0],
            "datetime": "2024-01-01/2024-01-31",
            "query": {"eo:cloud_cover": {"lt": 10}},
            "limit": 100
        }
        ingest = IngestModule(config)
        
        async for item in ingest.fetch(context):
            process_item(item)

Configuration:
    mode (str): Source mode - "file" or "api"
    source (str): File path (for file mode) or API URL (for api mode)
    format (str): File format - "json" or "parquet" (file mode only)
    collection_id (str, optional): STAC collection ID (api mode)
    bbox (list, optional): Bounding box filter [west, south, east, north]
    datetime (str, optional): Datetime filter (RFC 3339 or range)
    query (dict, optional): Additional query parameters
    limit (int, optional): Maximum items to fetch (default: 100)

See Also:
    - IngestConfig: Pydantic configuration model
    - Fetcher: Protocol interface implemented by this module
"""
import json
import asyncio
from pathlib import Path
from typing import AsyncIterator

from stac_manager.modules.config import IngestConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import ConfigurationError


class IngestModule:
    """Fetches STAC Items from local files or remote APIs.
    
    This module implements the Fetcher protocol and supports multiple ingestion modes:
    - File mode: Load items from local JSON or Parquet files
    - API mode: Fetch items from STAC API /search endpoints with filtering
    
    The module performs automatic format detection for JSON files (list or FeatureCollection),
    handles pagination for API requests, and collects failures in the workflow context.
    
    Attributes:
        config (IngestConfig): Validated configuration parameters
    
    Examples:
        Load from JSON file::

            ingest = IngestModule({
                "mode": "file",
                "source": "data/items.json",
                "format": "json"
            })
            
            async for item in ingest.fetch(context):
                print(item['id'])
        
        Fetch from STAC API with filters::

            ingest = IngestModule({
                "mode": "api",
                "source": "https://api.stac.com/v1",
                "collection_id": "my-collection",
                "bbox": [-180, -90, 180, 90],
                "limit": 50
            })
            
            async for item in ingest.fetch(context):
                process(item)
    """
    
    def __init__(self, config: dict) -> None:
        """Initialize IngestModule with configuration.
        
        Args:
            config: Configuration dictionary matching IngestConfig schema
        
        Raises:
            ConfigurationError: If file source doesn't exist (file mode)
            ValidationError: If config doesn't match IngestConfig schema
        """
        self.config = IngestConfig(**config)
        
        # Validate file exists for file mode
        if self.config.mode == "file":
            source_path = Path(self.config.source)
            if not source_path.exists():
                raise ConfigurationError(f"File not found: {self.config.source}")
    
    async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
        """Fetch STAC items from configured source.
        
        This async generator yields items one at a time, allowing for streaming
        processing of large datasets. For file sources, reads the entire file
        into memory. For API sources, handles pagination automatically.
        
        Args:
            context: Workflow context with failure collector and state
        
        Yields:
            dict: STAC Item dictionaries conforming to STAC specification
        
        Raises:
            DataProcessingError: On file read errors, API errors, or parsing failures
        
        Example:
            ::

                context = WorkflowContext.create()
                ingest = IngestModule(config)
                
                items = []
                async for item in ingest.fetch(context):
                    items.append(item)
                
                print(f"Loaded {len(items)} items")
        """
        if self.config.mode == "file":
            async for item in self._fetch_from_file():
                yield item
        else:
            async for item in self._fetch_from_api(context):
                yield item
    
    async def _fetch_from_file(self) -> AsyncIterator[dict]:
        """Fetch items from local file."""
        from stac_manager.exceptions import DataProcessingError
        
        try:
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
        except (FileNotFoundError, OSError, json.JSONDecodeError) as e:
            raise DataProcessingError(
                f"Failed to read file {self.config.source}: {e}"
            ) from e
    
    async def _fetch_from_api(self, context: WorkflowContext) -> AsyncIterator[dict]:
        """Fetch items from STAC API."""
        import pystac_client
        from stac_manager.exceptions import DataProcessingError
        
        # Resolve collection_id: Config overrides context (Matrix injection)
        collection_id = self.config.collection_id or context.data.get('collection_id')
        
        if not collection_id:
            raise ConfigurationError(
                "collection_id must be provided in config or context.data for API mode"
            )
        
        try:
            # Open STAC API client
            client = pystac_client.Client.open(self.config.source)
            
            # Build search parameters
            search_params = {
                "collections": [collection_id],  # Single collection as list
                "limit": self.config.limit,
            }
            
            if self.config.max_items:
                search_params["max_items"] = self.config.max_items
            
            # Add filter parameters
            if self.config.bbox:
                search_params["bbox"] = self.config.bbox
            
            if self.config.datetime:
                search_params["datetime"] = self.config.datetime
            
            if self.config.query:
                search_params["query"] = self.config.query
            
            # Execute search
            search = client.search(**search_params)
            
            # items_as_dicts() is a regular iterator, not async
            # Wrap in async iterator for consistency
            for item in search.items_as_dicts():
                yield item
                
        except ConnectionError as e:
            raise DataProcessingError(
                f"Failed to connect to STAC API at {self.config.source}: {e}"
            ) from e
        except Exception as e:
            raise DataProcessingError(
                f"Failed to fetch from STAC API: {e}"
            ) from e
