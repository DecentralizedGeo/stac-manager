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
        
    async def fetch(self, context: WorkflowContext) -> List[dict]:
        context.logger.debug(f"Discovery Config: {self.config}")
        
        # Store context for downstream modules (side effect)
        context.data['catalog_url'] = str(self.config.catalog_url)
        context.data['discovery_filters'] = self.config.filters.model_dump(exclude_none=True)
        
        client = Client.open(str(self.config.catalog_url))
        
        tasks = []
        if self.config.collection_ids:
            for coll_id in self.config.collection_ids:
                try:
                    # 1. Verify existence
                    collection = client.get_collection(coll_id)
                    if not collection:
                         context.logger.warning(f"Collection {coll_id} not found.")
                         continue
                    
                    # 2. Add Collection Context (Task)
                    tasks.append({
                        "type": "collection",
                        "collection_id": coll_id,
                        "collection_obj": collection,
                        "catalog_url": str(self.config.catalog_url)
                    })
                except Exception as e:
                     context.logger.error(f"Error discovering collection {coll_id}: {e}")
        else:
             context.logger.warning("No collection_ids configured for Discovery.")
             
        context.logger.info(f"Discovery complete. Found {len(tasks)} collections.")
        return tasks
