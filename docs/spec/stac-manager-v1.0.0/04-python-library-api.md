# Python Library API
## STAC Manager v1.0

**Related Documents**:
- [System Overview](./00-system-overview.md)

---

## 1. StacManager API

The highest level of abstraction is the `StacManager`, used to run declarative pipelines from Python code.

### 1.1 Class Definition
```python
from stac_manager.core import WorkflowContext
from stac_manager.config import WorkflowDefinition

class WorkflowResult:
    """Result of a workflow execution."""
    success: bool
    status: Literal['completed', 'completed_with_failures', 'failed']
    summary: str
    failure_count: int
    failures_path: str | None

class StacManager:
    """
    Main entry point for executing STAC Manager pipelines programmatically.
    """

    def __init__(self, config: dict | WorkflowDefinition):
        """
        Initialize manager with configuration.
        """
        ...

    async def execute(self) -> WorkflowResult:
        """
        Run the configured pipeline levels.
        """
        ...
```

### 1.2 Usage Example

```python
import asyncio
from stac_manager import StacManager

config = {
    "name": "programmatic-ingest",
    "steps": [
        {
            "id": "ingest",
            "module": "IngestModule",
            "config": {
                "collection_id": "landsat-c2-l2",
                "catalog_url": "https://cmr.earthdata.nasa.gov/stac/v1"
            }
        }
    ]
}

async def run():
    manager = StacManager(config)
    result = await manager.execute()
    print(f"Pipeline finished. Success: {result.success}")

if __name__ == "__main__":
    asyncio.run(run())
```

## 2. Module Composition API

Developers can use individual modules directly for custom script logic without the full orchestrator overhead.

```python
import asyncio
from stac_manager.modules import IngestModule, TransformModule, OutputModule
from stac_manager.core import WorkflowContext, FailureCollector, CheckpointManager

async def custom_pipeline():
    # Setup context
    ctx = WorkflowContext(
        workflow_id="custom-pipeline",
        config={}, 
        logger=..., 
        failure_collector=FailureCollector(),
        checkpoints=CheckpointManager(directory=Path('./checkpoints'), workflow_id="custom-pipeline"),
        data={}
    )

    # 1. Fetcher (Ingest)
    ingest = IngestModule({
        "collection_id": "landsat-c2-l2",
        "catalog_url": "..."
    })
    item_stream = await ingest.fetch(ctx)
    
    # 2. Sequential Processing
    async for item_dict in item_stream:
        # Transform Modifier (Sync)
        transform = TransformModule({"schema": ...})
        item_dict = transform.modify(item_dict, ctx)
        
        # Output Bundler (Sync)
        output = OutputModule({"output_path": "..."})
        output.bundle(item_dict, ctx)
    
    # Finalize
    result = output.finalize(ctx)
    return result
```

## 3. Utility Functions

The library exposes utilities reused across modules.

`stac_manager.utils.validation`
- `validate_stac_object(obj, schema_uri)`

`stac_manager.utils.geometry`
- `ensure_bbox(geometry)`: Calculates bbox if missing.

`stac_manager.utils.async_http`
- `fetch_with_retry(url, session, retries)`
