"""Output Module - Write STAC Items to disk."""
import json
import asyncio
from pathlib import Path
from typing import Optional

from stac_manager.modules.config import OutputConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import ConfigurationError


class OutputModule:
    """Writes STAC Items to JSON or Parquet files in STAC collection structure."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with configuration."""
        self.config = OutputConfig(**config)
        self.buffer: list[dict] = []
        self.items_written = 0
        self.collection_id: Optional[str] = None
        self.collection_created = False
    
    async def bundle(self, item: dict, context: WorkflowContext) -> None:
        """
        Accept a single item for bundling.
        
        Items are buffered and flushed when buffer_size is reached.
        Creates collection.json on first item if not already created.
        
        Args:
            item: STAC item dict
            context: Workflow context
        """
        # Extract collection_id from first item or context
        if self.collection_id is None:
            self.collection_id = item.get("collection") or context.data.get("collection_id", "default")
        
        # Create collection.json on first item
        if not self.collection_created:
            await self._create_collection(context)
            self.collection_created = True
        
        # Add relative self link to item
        item = self._add_item_links(item)
        
        self.buffer.append(item)
        
        # Auto-flush when buffer is full
        if len(self.buffer) >= self.config.buffer_size:
            await self._flush(context)
    
    async def finalize(self, context: WorkflowContext) -> dict:
        """
        Finalize output and return manifest.
        
        Flushes any remaining buffered items.
        
        Args:
            context: Workflow context
            
        Returns:
            Manifest dict with items_written count
        """
        # Flush remaining items
        await self._flush(context)
        
        return {
            "items_written": self.items_written
        }
    
    async def _flush(self, context: WorkflowContext) -> None:
        """Flush buffered items to disk."""
        if not self.buffer:
            return
        
        if self.config.format == "json":
            await self._flush_json(context)
        elif self.config.format == "parquet":
            await self._flush_parquet(context)
    
    async def _flush_json(self, context: WorkflowContext) -> None:
        """Write items as individual JSON files with atomic writes."""
        import os
        
        # base_dir/collection_id/items/
        collection_dir = Path(self.config.base_dir) / str(self.collection_id)
        items_dir = collection_dir / "items"
        
        # Create directory if missing
        await asyncio.to_thread(items_dir.mkdir, parents=True, exist_ok=True)
        
        # Write each item
        for item in self.buffer:
            item_id = item.get("id", "unknown")
            item_path = items_dir / f"{item_id}.json"
            temp_path = items_dir / f"{item_id}.json.tmp"
            
            try:
                # Write to temp file
                content = json.dumps(item, indent=2)
                await asyncio.to_thread(temp_path.write_text, content)
                
                # Atomic rename
                await asyncio.to_thread(os.replace, str(temp_path), str(item_path))
                
                self.items_written += 1
                
            except Exception:
                # Clean up temp file on error
                if temp_path.exists():
                    await asyncio.to_thread(temp_path.unlink)
                raise
        
        # Clear buffer
        self.buffer.clear()
    
    async def _flush_parquet(self, context: WorkflowContext) -> None:
        """Write items as Parquet file."""
        import pyarrow as pa
        import pyarrow.parquet as pq
        import os
        from datetime import datetime
        
        if not self.buffer:
            return
        
        # base_dir/collection_id/items/
        collection_dir = Path(self.config.base_dir) / str(self.collection_id)
        items_dir = collection_dir / "items"
        
        # Create directory if missing
        await asyncio.to_thread(items_dir.mkdir, parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        parquet_path = items_dir / f"items_{timestamp}.parquet"
        temp_path = items_dir / f"items_{timestamp}.parquet.tmp"
        
        try:
            # Convert items to Arrow Table
            table = await asyncio.to_thread(pa.Table.from_pylist, self.buffer)
            
            # Write to temp file
            await asyncio.to_thread(pq.write_table, table, str(temp_path))
            
            # Atomic rename
            await asyncio.to_thread(os.replace, str(temp_path), str(parquet_path))
            
            self.items_written += len(self.buffer)
            
        except Exception:
            # Clean up temp file on error
            if temp_path.exists():
                await asyncio.to_thread(temp_path.unlink)
            raise
        
        # Clear buffer
        self.buffer.clear()
    
    def _add_item_links(self, item: dict) -> dict:
        """
        Add relative self and collection links to item.
        
        Creates self-contained catalog structure with relative paths.
        
        Args:
            item: STAC item dict
            
        Returns:
            Item with added links
        """
        item = item.copy()
        
        # Ensure links array exists
        if "links" not in item:
            item["links"] = []
        
        # Remove existing self/parent/collection links to avoid duplicates
        item["links"] = [
            link for link in item["links"]
            if link.get("rel") not in ["self", "parent", "collection"]
        ]
        
        # Add relative self link
        item["links"].append({
            "rel": "self",
            "href": f"./items/{item['id']}.json",
            "type": "application/json"
        })
        
        # Add relative parent link (collection)
        item["links"].append({
            "rel": "parent",
            "href": "../collection.json",
            "type": "application/json"
        })
        
        # Add relative collection link
        item["links"].append({
            "rel": "collection",
            "href": "../collection.json",
            "type": "application/json"
        })
        
        return item
    
    async def _create_collection(self, context: WorkflowContext) -> None:
        """
        Create collection.json file for the collection.
        
        Only created once per collection. Uses minimal STAC Collection structure
        with relative links to items directory.
        
        Args:
            context: Workflow context
        """
        collection_dir = Path(self.config.base_dir) / str(self.collection_id)
        collection_path = collection_dir / "collection.json"
        
        # Skip if collection.json already exists
        if await asyncio.to_thread(collection_path.exists):
            return
        
        # Create collection directory
        await asyncio.to_thread(collection_dir.mkdir, parents=True, exist_ok=True)
        
        # Build minimal collection structure
        collection = {
            "type": "Collection",
            "stac_version": "1.0.0",
            "id": str(self.collection_id),
            "description": f"STAC Collection: {self.collection_id}",
            "license": "proprietary",
            "extent": {
                "spatial": {"bbox": [[-180, -90, 180, 90]]},
                "temporal": {"interval": [[None, None]]}
            },
            "links": [
                {
                    "rel": "self",
                    "href": "./collection.json",
                    "type": "application/json"
                },
                {
                    "rel": "items",
                    "href": "./items/",
                    "type": "application/json"
                }
            ]
        }
        
        # Write collection.json atomically
        temp_path = collection_dir / "collection.json.tmp"
        
        try:
            content = json.dumps(collection, indent=2)
            await asyncio.to_thread(temp_path.write_text, content)
            
            import os
            await asyncio.to_thread(os.replace, str(temp_path), str(collection_path))
            
        except Exception:
            if temp_path.exists():
                await asyncio.to_thread(temp_path.unlink)
            raise
