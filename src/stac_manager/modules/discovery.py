from typing import AsyncIterator, List, Optional
from pydantic import BaseModel, HttpUrl
from pystac_client import Client
from stac_manager.context import WorkflowContext

class DiscoveryConfig(BaseModel):
    catalog_url: HttpUrl
    collection_ids: Optional[List[str]] = None

class DiscoveryModule:
    """Fetcher that discovers collections from a STAC API."""
    
    def __init__(self, config: dict):
        self.config = DiscoveryConfig(**config)
        
    async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
        # Store catalog_url for downstream modules
        context.data['catalog_url'] = str(self.config.catalog_url)
        
        # Note: In real sync implementation, block fetching might block the loop 
        # unless moved to executor, but pystac-client is sync.
        # For this phase, we run it directly or wrap in thread. 
        # Spec says Fetchers are async. pystac-client is sync.
        # Ideally we wrap this. For simplicity here, we assume sync call is fast enough for discovery.
        
        client = Client.open(str(self.config.catalog_url))
        collections = client.get_collections()
        
        for collection in collections:
            if self.config.collection_ids:
                if collection.id not in self.config.collection_ids:
                    continue
            yield collection.to_dict()
