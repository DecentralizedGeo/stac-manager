from typing import AsyncIterator, Optional
from pydantic import BaseModel
from pystac_client import Client
from stac_manager.context import WorkflowContext
from stac_manager.exceptions import ModuleException

class IngestConfig(BaseModel):
    collection_id: Optional[str] = None
    # Add other search filters here as needed

class IngestModule:
    """Fetcher that retrieves items from a STAC API for a specific collection."""
    
    def __init__(self, config: dict):
        self.config = IngestConfig(**config)
    
    async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
        # 1. Resolve Catalog URL
        catalog_url = context.data.get('catalog_url')
        if not catalog_url:
            raise ModuleException("IngestModule requires 'catalog_url' in context.data (usually from DiscoveryModule)")
        
        # 2. Resolve Collection ID
        # Priority: context (from parallel orchestrator) > config > error
        collection_id = context.data.get('_current_collection_id') or self.config.collection_id
        
        if not collection_id:
            # If still None, maybe we search all? Spec implies per-collection pipeline.
            # Let's permit it but warn, or default to all.
            pass

        client = Client.open(catalog_url)
        search = client.search(collections=[collection_id] if collection_id else None)
        
        # Iterator
        for item in search.items():
            yield item.to_dict()
