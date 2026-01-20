from typing import AsyncIterator, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from pystac_client import Client
from stac_manager.context import WorkflowContext
from stac_manager.exceptions import ModuleException

class IngestFilters(BaseModel):
    temporal: Optional[Dict[str, str]] = None
    spatial: Optional[List[float]] = None
    query: Optional[Dict[str, Any]] = None

class IngestConfig(BaseModel):
    collection_id: Optional[str] = None
    source_file: Optional[str] = None
    limit: Optional[int] = Field(None, gt=0)
    concurrency: int = Field(default=5, ge=1)
    rate_limit: float = Field(default=10.0, gt=0)
    filters: IngestFilters = Field(default_factory=IngestFilters)

class IngestModule:
    """Fetcher that retrieves items from a STAC API for a specific collection."""
    
    def __init__(self, config: dict):
        self.config = IngestConfig(**config)
    
    async def fetch(self, context: WorkflowContext, items: AsyncIterator[dict] = None) -> AsyncIterator[dict]:
        context.logger.info(f"Ingesting with config: {self.config}")
        
        # 1. Source File Mode
        if self.config.source_file:
            context.logger.info(f"Ingesting from source file: {self.config.source_file}")
            for item in self.fetch_from_file(self.config.source_file, context):
                yield item
            return
            
        # 2. STAC API Mode (existing logic)
        if not items:
            context.logger.warning("IngestModule received no input tasks and no source_file configured.")
            return

        # Normalize input to async iterator if it's a list
        if isinstance(items, list):
            async def _list_to_async_gen(data):
                for item in data:
                    yield item
            items = _list_to_async_gen(items)

        total_count = 0
        client = None
        current_catalog_url = None
        
        # Iterate over the Tasks (streams of collections)
        async for task in items:
            collection_obj = task.get("collection_obj")
            collection_id = task.get("collection_id")
            catalog_url = task.get("catalog_url") or context.data.get('catalog_url')
            
            if not collection_obj:
                continue

            # Lazy Client Initialization / Re-initialization if URL changes
            if catalog_url and catalog_url != current_catalog_url:
                current_catalog_url = catalog_url
                client = Client.open(catalog_url)
            
            if not client:
                 context.logger.error(f"Cannot ingest from {collection_id}: No catalog_url found in task or context.")
                 continue

            context.logger.info(f"Executing search for collection: {collection_id}")
            
            try:
                # Build Search Params from Ingest Config
                search_params = {
                    "collections": [collection_obj],
                    "max_items": self.config.limit 
                }
                
                # Apply Filters from Ingest Config
                if self.config.filters.spatial:
                     search_params["bbox"] = self.config.filters.spatial
                if self.config.filters.query:
                     search_params["query"] = self.config.filters.query
                # Temporal filtering etc.
                if self.config.filters.temporal:
                     # Simple pass-through or parsing
                     pass

                # Execute Search
                search_obj = client.search(**search_params)
                
                item_count = 0
                for item_dict in search_obj.items_as_dicts():
                    yield item_dict
                    item_count += 1
                    total_count += 1
            except Exception as e:
                context.logger.error(f"Error fetching items for {collection_id}: {e}")
                continue
            
            context.logger.info(f"Finished collection {collection_id}: {item_count} items")

        context.logger.info(f"Ingest complete. Total items fetched: {total_count}")

    def fetch_from_file(self, path: str, context: WorkflowContext):
        import json
        import os
        
        if not os.path.exists(path):
            context.logger.error(f"Source file not found: {path}")
            return

        if path.endswith(".parquet"):
             # Optional: import stac_geoparquet
             # For now, just log warning or error if dependencies missing
             context.logger.warning("Parquet support not fully implemented in this iteration.")
             return 
        else:
            try:
                with open(path) as f:
                    data = json.load(f)
                
                if isinstance(data, dict):
                    if data.get("type") == "FeatureCollection":
                        yield from data.get("features", [])
                    else:
                        yield data
                elif isinstance(data, list):
                    yield from data
            except Exception as e:
                context.logger.error(f"Error reading source file {path}: {e}")
