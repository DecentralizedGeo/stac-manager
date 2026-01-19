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
    
    async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
        context.logger.info(f"Ingesting with config: {self.config}")
        
        # 1. Resolve Catalog URL
        catalog_url = context.data.get('catalog_url')
        if not catalog_url:
            raise ModuleException("IngestModule requires 'catalog_url' in context.data (usually from DiscoveryModule)")
        
        # 2. Resolve Collection ID
        # Priority: context (from parallel orchestrator) > config > error
        collection_id = context.data.get('_current_collection_id') or self.config.collection_id
        
        if collection_id:
            context.logger.info(f"Ingesting from collection: {collection_id}")
        else:
            context.logger.warning("No collection_id resolved for IngestModule")

        client = Client.open(catalog_url)
        
        # Build Search Parameters
        search_params = {
            "collections": [collection_id] if collection_id else None,
            "max_items": self.config.limit
        }
        
        context.logger.debug(f"Search parameters: {search_params}")
        
        # Apply filters
        if self.config.filters.spatial:
            search_params["bbox"] = self.config.filters.spatial
        if self.config.filters.temporal:
            # Assuming temporal is dict like {"start": "...", "end": "..."} or ISO string
            # pystac-client expects "start/end" string or list
            # We'll stick to a simple pass-through if it's already a string, or format it
            # For now, simplistic handling:
            pass 
        if self.config.filters.query:
             search_params["query"] = self.config.filters.query

        search = client.search(**search_params)
        
        # Iterator
        count = 0
        for item in search.items():
            context.logger.debug(f"Yielding item {item.id}")
            count += 1
            yield item.to_dict()
            
        context.logger.info(f"Ingest complete. Total items fetched: {count}")
