from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl, Field
import pystac
from pystac import utils as pystac_utils
from stac_manager.context import WorkflowContext
import datetime
from stac_manager.utils import ensure_bbox

class Provider(BaseModel):
    name: str
    roles: List[str]
    url: Optional[HttpUrl] = None

class DefaultsConfig(BaseModel):
    license: str = "CC-BY-4.0"
    providers: List[Provider] = []
    geometry: Optional[Dict] = None

class ScaffoldConfig(BaseModel):
    mode: Literal['items', 'collection', 'catalog'] = 'items'
    collection_id: Optional[str] = None
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)

class ScaffoldModule:
    """Scaffolds intermediate data into valid PySTAC objects."""
    
    def __init__(self, config: dict):
        self.config = ScaffoldConfig(**config)
        
    def modify(self, item: dict, context: WorkflowContext) -> dict | None:
        if self.config.mode != 'items':
            # TODO: Implement collection/catalog generation mode
            context.logger.warning(f"Scaffold mode {self.config.mode} not supported yet")
            return None

        # 1. Create PySTAC Item
        try:
            # Extract core fields
            oid = item.get('id')
            props = item.get('properties', {})
            geom = item.get('geometry') or self.config.defaults.geometry
            dt_str = props.get('datetime')
            
            if not oid or not geom:
                # Log failure
                context.logger.warning(f"Scaffold failed: Missing id or geometry for item {oid}")
                return None
                
            # Parse datetime if string
            dt = None
            if dt_str:
                if isinstance(dt_str, str):
                    dt = pystac_utils.str_to_datetime(dt_str)
                elif isinstance(dt_str, datetime.datetime):
                    dt = dt_str
            
            if not dt:
                 context.logger.warning(f"Scaffold failed: Missing datetime for item {oid}")
                 return None

            context.logger.debug(f"Scaffolding item {oid} with geom type {type(geom)}")

            pystac_item = pystac.Item(
                id=oid,
                geometry=geom,
                bbox=ensure_bbox(geom), 
                datetime=dt,
                properties=props
            )
            
            # Apply defaults (collection_id)
            if self.config.collection_id:
                pystac_item.collection_id = self.config.collection_id
            
            # Apply license/providers (simple placeholder logic)
            # In V1.0, we just ensure the valid item structure. 
            # License/Providers usually belong to Collection, but we can add to properties if needed.
            if self.config.defaults.license:
                pystac_item.properties['license'] = self.config.defaults.license
                
            return pystac_item.to_dict()
            
        except Exception as e:
            context.logger.error(f"Scaffold unexpected error for item {item.get('id')}: {e}", exc_info=True)
            # context.failure_collector.add(item.get('id', 'unknown'), str(e), step_id='scaffold')
            return None
