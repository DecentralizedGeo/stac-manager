from typing import AsyncIterator, List, Dict, Any, Optional
from pydantic import BaseModel
from stac_manager.context import WorkflowContext

class StaticSourceConfig(BaseModel):
    items: List[Dict[str, Any]]

class StaticSourceModule:
    """Fetcher that yields static items from config."""
    
    def __init__(self, config: dict):
        self.config = StaticSourceConfig(**config)
    
    async def fetch(self, context: Optional[WorkflowContext] = None) -> AsyncIterator[dict]:
        for item in self.config.items:
            yield item
