"""Output Module - Write STAC Items to disk."""
import json
import asyncio
from pathlib import Path
from typing import Optional

from stac_manager.modules.config import OutputConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import ConfigurationError


class OutputModule:
    """Writes STAC Items to JSON or Parquet files."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with configuration."""
        self.config = OutputConfig(**config)
        self.buffer: list[dict] = []
        self.items_written = 0
    
    async def bundle(self, item: dict, context: WorkflowContext) -> None:
        """
        Accept a single item for bundling.
        
        Items are buffered and flushed when buffer_size is reached.
        
        Args:
            item: STAC item dict
            context: Workflow context
        """
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
        
        output_dir = Path(self.config.base_dir)
        
        # Create directory if missing
        await asyncio.to_thread(output_dir.mkdir, parents=True, exist_ok=True)
        
        # Write each item
        for item in self.buffer:
            item_id = item.get("id", "unknown")
            item_path = output_dir / f"{item_id}.json"
            temp_path = output_dir / f"{item_id}.json.tmp"
            
            try:
                # Write to temp file
                content = json.dumps(item, indent=2)
                await asyncio.to_thread(temp_path.write_text, content)
                
                # Atomic rename
                await asyncio.to_thread(os.replace, str(temp_path), str(item_path))
                
                self.items_written += 1
                
            except Exception as e:
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
        
        output_dir = Path(self.config.base_dir)
        
        # Create directory if missing
        await asyncio.to_thread(output_dir.mkdir, parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        parquet_path = output_dir / f"items_{timestamp}.parquet"
        temp_path = output_dir / f"items_{timestamp}.parquet.tmp"
        
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
