from typing import AsyncIterator, List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, Field
from pystac_client import Client
from stac_manager.context import WorkflowContext

class DiscoveryFilters(BaseModel):
    temporal: Optional[Dict[str, Any]] = None
    spatial: Optional[List[float]] = None

class DiscoveryConfig(BaseModel):
    catalog_url: HttpUrl
    collection_ids: Optional[List[str]] = None
    filters: DiscoveryFilters = Field(default_factory=DiscoveryFilters)

class DiscoveryModule:
    """Fetcher that discovers collections from a STAC API."""
    
    def __init__(self, config: dict):
        self.config = DiscoveryConfig(**config)
        
    async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
        context.logger.debug(f"Discovery Config: {self.config}")
        # Store catalog_url/client info for downstream modules
        # This fulfills the "Side Effects" contract
        context.data['catalog_url'] = str(self.config.catalog_url)
        context.data['discovery_filters'] = self.config.filters.model_dump(exclude_none=True)
        if self.config.filters.temporal:
            context.logger.debug(f"Applied temporal filter configuration: {self.config.filters.temporal}")
        
        # Note: In real sync implementation, block fetching might block the loop 
        # unless moved to executor, but pystac-client is sync.
        # For this phase, we run it directly or wrap in thread. 
        # Spec says Fetchers are async. pystac-client is sync.
        # Ideally we wrap this. For simplicity here, we assume sync call is fast enough for discovery.
        
        client = Client.open(str(self.config.catalog_url))
        collections = client.get_collection()
        
        count = 0
        for collection in collections:
            context.logger.debug(f"Scanning collection {collection.id}")
            if self.config.collection_ids:
                if collection.id not in self.config.collection_ids:
                    continue
            count += 1
            yield collection.to_dict()
            
        context.logger.info(f"Total collections found: {count}")
