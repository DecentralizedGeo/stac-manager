"""Ingest Module - Fetch STAC Items from files or APIs.

This module provides the IngestModule class for loading STAC items from various sources
including local JSON/Parquet files, item directories, STAC collections, and remote STAC
API endpoints.

Example:
    Basic file ingestion::

        from stac_manager.modules.ingest import IngestModule
        from stac_manager.core.context import WorkflowContext
        
        # Load from JSON file
        config = {
            "mode": "file",
            "source": "items.json"
        }
        ingest = IngestModule(config)
        
        context = WorkflowContext.create()
        async for item in ingest.fetch(context):
            print(f"Loaded item: {item['id']}")
    
    Load from items directory::

        # Auto-detects directory of JSON items
        config = {
            "mode": "file",
            "source": "./data/items"  # Directory with *.json files
        }
    
    Load from STAC collection::

        # Point to collection root (has collection.json + items/)
        config = {
            "mode": "file",
            "source": "./data/my-collection"
        }
        
        # Or point directly to collection.json
        config = {
            "mode": "file",
            "source": "./data/my-collection/collection.json"
        }
    
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
    source (str): File/directory path or API URL
    source_type (str, optional): Source type - "auto", "file", "items_directory", "collection"
    format (str, optional): File format - "json" or "parquet" (auto-detected if not specified)
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
import logging
from pathlib import Path
from typing import AsyncIterator

from stac_manager.modules.config import IngestConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class IngestModule:
    """Fetches STAC Items from local files or remote APIs.
    
    This module implements the Fetcher protocol and supports multiple ingestion modes:
    
    File mode:
        - Single JSON file (list or FeatureCollection)
        - Single Parquet file
        - Items directory (multiple JSON files)
        - STAC collection root (has collection.json + items/)
        - Direct collection.json reference
    
    API mode:
        - Fetch items from STAC API /search endpoints with filtering
    
    The module performs automatic source type detection, handles pagination for API
    requests, and collects failures in the workflow context.
    
    Attributes:
        config (IngestConfig): Validated configuration parameters
    
    Examples:
        Load from items directory::

            ingest = IngestModule({
                "mode": "file",
                "source": "./data/items"  # Auto-detects directory
            })
            
            async for item in ingest.fetch(context):
                print(item['id'])
        
        Load from collection root::

            ingest = IngestModule({
                "mode": "file",
                "source": "./data/my-collection",  # Has collection.json + items/
                "source_type": "collection"  # Optional: be explicit
            })
        
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
        self.logger = logging.getLogger(__name__)  # Default logger
        
        # Validate file exists for file mode
        if self.config.mode == "file":
            source_path = Path(self.config.source)
            if not source_path.exists():
                raise ConfigurationError(f"File not found: {self.config.source}")
    
    def set_logger(self, logger: logging.Logger) -> None:
        """Set step-specific logger for this module.
        
        Args:
            logger: Logger instance to use for this module
        """
        self.logger = logger
    
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
        # Log start with INFO level
        self.logger.info(
            f"Starting ingest | mode: {self.config.mode} | source: {self.config.source}"
        )
        
        count = 0
        if self.config.mode == "file":
            async for item in self._fetch_from_file():
                if item is None:
                    continue
                self.logger.debug(f"Fetched item {item.get('id', 'unknown')}")
                yield item
                count += 1
        else:
            async for item in self._fetch_from_api(context):
                if item is None:
                    continue
                self.logger.debug(f"Fetched item {item.get('id', 'unknown')}")
                yield item
                count += 1
        
        # Log completion with INFO level
        self.logger.info(f"Ingest complete | total_items: {count}")
    
    async def _fetch_from_file(self) -> AsyncIterator[dict]:
        """Fetch items from local file or directory with smart detection."""
        source_path = Path(self.config.source)
        
        # Determine source type (explicit or auto-detect)
        source_type = self._determine_source_type(source_path)
        self.logger.debug(f"Detected source_type: {source_type} for {source_path}")
        
        # Route to appropriate handler
        if source_type == "items_directory":
            async for item in self._load_items_from_directory(source_path):
                yield item
        elif source_type == "collection":
            async for item in self._load_collection_source(source_path):
                yield item
        else:  # "file"
            async for item in self._load_single_file(source_path):
                yield item
    
    def _determine_source_type(self, path: Path) -> str:
        """Determine source type from config or auto-detection.
        
        Args:
            path: Source path to analyze
        
        Returns:
            Source type: "file", "items_directory", or "collection"
        
        Raises:
            ConfigurationError: If source_type is invalid for the given path
        """
        # Use explicit source_type if provided
        if self.config.source_type and self.config.source_type != "auto":
            # Validate explicit type matches reality
            if self.config.source_type == "file" and path.is_dir():
                raise ConfigurationError(
                    f"source_type='file' specified but {path} is a directory"
                )
            if self.config.source_type in ["items_directory", "collection"] and not path.is_dir():
                # Allow collection type for collection.json files
                if not (self.config.source_type == "collection" and path.name == "collection.json"):
                    raise ConfigurationError(
                        f"source_type='{self.config.source_type}' specified but {path} is not a directory"
                    )
            return self.config.source_type
        
        # Auto-detect source type
        if path.is_dir():
            # Check if it's a STAC collection root
            if (path / "collection.json").exists():
                logger.debug(f"Found collection.json in {path}, treating as collection root")
                return "collection"
            else:
                # Assume it's an items directory
                return "items_directory"
        elif path.is_file():
            # Special case: collection.json file
            if path.name == "collection.json":
                return "collection"
            else:
                return "file"
        else:
            raise ConfigurationError(f"Source path does not exist: {path}")
    
    async def _load_items_from_directory(self, directory: Path) -> AsyncIterator[dict]:
        """Load all JSON items from a directory.
        
        Args:
            directory: Directory containing item JSON files
        
        Yields:
            STAC Item dictionaries
        
        Raises:
            DataProcessingError: If no items found or all items fail to load
        """
        from stac_manager.exceptions import DataProcessingError
        
        json_files = sorted(directory.glob("*.json"))
        
        if not json_files:
            raise DataProcessingError(f"No JSON files found in directory: {directory}")
        
        logger.info(f"Loading {len(json_files)} items from {directory}")
        
        loaded_count = 0
        failed_count = 0
        
        for json_file in json_files:
            try:
                content = await asyncio.to_thread(json_file.read_text, encoding='utf-8')
                item = json.loads(content)
                yield item
                loaded_count += 1
            except (OSError, json.JSONDecodeError) as e:
                failed_count += 1
                logger.warning(f"Failed to read {json_file.name}: {e}")
                continue
        
        if loaded_count == 0:
            raise DataProcessingError(
                f"All {failed_count} items in {directory} failed to load"
            )
        
        if failed_count > 0:
            logger.warning(f"Loaded {loaded_count} items, {failed_count} failed from {directory}")
    
    async def _load_collection_source(self, source_path: Path) -> AsyncIterator[dict]:
        """Load items from a STAC collection source.
        
        Handles two cases:
        1. Path is a collection root directory (has collection.json + items/)
        2. Path is a collection.json file directly
        
        Args:
            source_path: Collection root directory or collection.json file
        
        Yields:
            STAC Item dictionaries
        
        Raises:
            ConfigurationError: If collection structure is invalid
        """
        # Determine items directory location
        if source_path.is_dir():
            # Collection root directory
            items_dir = source_path / "items"
            collection_file = source_path / "collection.json"
        else:
            # Direct collection.json file
            items_dir = source_path.parent / "items"
            collection_file = source_path
        
        # Check if items directory exists
        if items_dir.exists() and items_dir.is_dir():
            logger.info(f"Loading items from collection at {source_path}")
            async for item in self._load_items_from_directory(items_dir):
                yield item
        else:
            # Try to load inline items from collection.json
            logger.debug(f"No items/ directory found, checking for inline items in {collection_file}")
            try:
                content = await asyncio.to_thread(collection_file.read_text, encoding='utf-8')
                collection_data = json.loads(content)
                
                # Check for inline features
                if "features" in collection_data:
                    logger.info(f"Loading inline items from {collection_file}")
                    for item in collection_data["features"]:
                        yield item
                else:
                    raise ConfigurationError(
                        f"No items/ directory found and no inline features in {collection_file}"
                    )
            except (OSError, json.JSONDecodeError) as e:
                raise ConfigurationError(
                    f"Failed to read collection file {collection_file}: {e}"
                ) from e
    
    async def _load_single_file(self, file_path: Path) -> AsyncIterator[dict]:
        """Load items from a single file (JSON or Parquet).
        
        Args:
            file_path: Path to JSON or Parquet file
        
        Yields:
            STAC Item dictionaries
        
        Raises:
            DataProcessingError: On file read errors or parsing failures
        """
        from stac_manager.exceptions import DataProcessingError
        
        # Determine format from file extension or config
        file_format = self.config.format
        if not file_format:
            suffix = file_path.suffix.lower()
            if suffix == ".json":
                file_format = "json"
            elif suffix == ".parquet":
                file_format = "parquet"
            else:
                raise ConfigurationError(
                    f"Cannot determine format for file: {file_path}. "
                    f"Specify 'format' in config or use .json/.parquet extension."
                )
        
        try:
            if file_format == "json":
                async for item in self._load_json_file(file_path):
                    yield item
            elif file_format == "parquet":
                async for item in self._load_parquet_file(file_path):
                    yield item
            else:
                raise ConfigurationError(f"Unsupported format: {file_format}")
        except (FileNotFoundError, OSError) as e:
            raise DataProcessingError(
                f"Failed to read file {file_path}: {e}"
            ) from e
    
    async def _load_json_file(self, file_path: Path) -> AsyncIterator[dict]:
        """Load items from a single JSON file.
        
        Supports:
        - FeatureCollection format
        - Array of items
        - Single item object
        
        Args:
            file_path: Path to JSON file
        
        Yields:
            STAC Item dictionaries
        
        Raises:
            DataProcessingError: On JSON parsing errors
        """
        from stac_manager.exceptions import DataProcessingError
        
        try:
            content = await asyncio.to_thread(file_path.read_text, encoding='utf-8')
            data = json.loads(content)
            
            # Handle FeatureCollection
            if isinstance(data, dict) and data.get("type") == "FeatureCollection":
                items = data.get("features", [])
                self.logger.info(f"Loading {len(items)} items from FeatureCollection in {file_path}")
                for item in items:
                    yield item
            # Handle array of items
            elif isinstance(data, list):
                self.logger.info(f"Loading {len(data)} items from array in {file_path}")
                for item in data:
                    yield item
            # Handle single item
            else:
                self.logger.info(f"Loading single item from {file_path}")
                yield data
        except json.JSONDecodeError as e:
            raise DataProcessingError(
                f"Invalid JSON in {file_path}: {e}"
            ) from e
    
    async def _load_parquet_file(self, file_path: Path) -> AsyncIterator[dict]:
        """Load items from a Parquet file.
        
        Args:
            file_path: Path to Parquet file
        
        Yields:
            STAC Item dictionaries
        
        Raises:
            DataProcessingError: On Parquet read errors
        """
        from stac_manager.exceptions import DataProcessingError
        
        try:
            import pyarrow.parquet as pq
        except ImportError:
            raise DataProcessingError(
                "pyarrow is required to read Parquet files. Install with: pip install pyarrow"
            )
        
        try:
            # Use thread pool for blocking I/O
            table = await asyncio.to_thread(pq.read_table, str(file_path))
            items = table.to_pylist()
            
            self.logger.info(f"Loading {len(items)} items from Parquet file {file_path}")
            
            for item in items:
                yield item
        except Exception as e:
            raise DataProcessingError(
                f"Failed to read Parquet file {file_path}: {e}"
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
