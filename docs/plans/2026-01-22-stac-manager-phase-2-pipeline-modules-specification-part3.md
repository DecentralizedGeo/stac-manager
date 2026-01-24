# STAC Manager Phase 2 (Pipeline Modules) Implementation Plan - Part 3

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

> **Context**: This is **Part 3 of Phase 2: Pipeline Modules** of the STAC Manager implementation.  
> See [Implementation Roadmap](./2026-01-22-stac-manager-roadmap.md), [Part 1](./2026-01-22-stac-manager-phase-2-pipeline-modules-specification-part1.md), and [Part 2](./2026-01-22-stac-manager-phase-2-pipeline-modules-specification-part2.md) for complete context.

**Goal**: Implement I/O-heavy pipeline components (IngestModule, OutputModule) and end-to-end integration tests to validate the complete pipeline architecture.

**Architecture**: Fetcher + Bundler protocol implementations with async I/O
- **IngestModule**: API/File fetching with parallelism and rate limiting (Fetcher Protocol)
- **OutputModule**: JSON/Parquet output with atomic writes (Bundler Protocol)
- **Integration**: End-to-end module interoperability validation

**Tech Stack**: 
- Python 3.12+, pystac-client, httpx (async HTTP)
- stac-geoparquet, pyarrow (Parquet I/O), aiofiles (async file ops)
- pytest, pytest-asyncio, pytest-mock, pytest-cov

**Dependencies**: 
- Part 1 complete (Core Infrastructure, SeedModule, UpdateModule)
- Part 2 complete (ValidateModule, ExtensionModule, TransformModule)
- Phase 1 utilities (`stac_manager/utils/`)

---

## Table of Contents

### Phase 7: Ingest Module (Tasks 36-44) - 9 tasks
API and file-based fetching with internal parallelism

### Phase 8: Output Module (Tasks 45-51) - 7 tasks  
JSON and Parquet output with buffering and atomic writes

### Phase 9: Integration & Verification (Tasks 52-56) - 5 tasks
End-to-end testing and documentation

**Total Tasks**: 21 granular TDD tasks

---

## Phase 7: Ingest Module

### Task 36: Ingest Module - File Mode (JSON)

**Files:**
- Create: `src/stac_manager/modules/ingest.py`
- Create: `tests/unit/modules/test_ingest.py`
- Modify: `src/stac_manager/modules/__init__.py`
- Modify: `src/stac_manager/modules/config.py`

**Step 1: Write failing test for JSON file ingestion**

Create `tests/unit/modules/test_ingest.py`:

```python
import pytest
import json
from pathlib import Path
from tests.fixtures.context import MockWorkflowContext
from tests.fixtures.stac_items import VALID_ITEM
from stac_manager.modules.ingest import IngestModule


@pytest.mark.asyncio
async def test_ingest_json_file_success(tmp_path):
    """IngestModule reads items from JSON file."""
    # Create test JSON file with item list
    items_file = tmp_path / "items.json"
    test_items = [VALID_ITEM.copy(), {**VALID_ITEM, "id": "test-item-002"}]
    items_file.write_text(json.dumps(test_items))
    
    # Configure module for file mode
    config = {
        "mode": "file",
        "source": str(items_file),
        "format": "json"
    }
    module = IngestModule(config)
    context = MockWorkflowContext.create()
    
    # Fetch items
    results = [item async for item in module.fetch(context)]
    
    assert len(results) == 2
    assert results[0]["id"] == "test-item-001"
    assert results[1]["id"] == "test-item-002"


@pytest.mark.asyncio
async def test_ingest_json_file_not_found():
    """IngestModule raises ConfigurationError for missing file."""
    config = {
        "mode": "file",
        "source": "/nonexistent/items.json",
        "format": "json"
    }
    
    from stac_manager.exceptions import ConfigurationError
    with pytest.raises(ConfigurationError, match="File not found"):
        module = IngestModule(config)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_ingest.py::test_ingest_json_file_success -v`  
Expected: FAIL with "ModuleNotFoundError: No module named 'stac_manager.modules.ingest'"

**Step 3: Create config model for IngestModule**

Add to `src/stac_manager/modules/config.py`:

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional


class IngestConfig(BaseModel):
    """Configuration for IngestModule."""
    mode: Literal["file", "api"] = Field(description="Ingestion mode")
    source: str = Field(description="File path or API URL")
    format: Optional[Literal["json", "parquet"]] = Field(default="json", description="File format (file mode only)")
    collections: Optional[list[str]] = Field(default=None, description="Collections to search (API mode)")
    bbox: Optional[list[float]] = Field(default=None, description="Bounding box filter")
    datetime: Optional[str] = Field(default=None, description="Datetime filter")
    query: Optional[dict] = Field(default=None, description="CQL query")
    limit: Optional[int] = Field(default=100, description="Items per page")
    max_items: Optional[int] = Field(default=None, description="Maximum items to fetch")
```

**Step 4: Implement basic IngestModule structure**

Create `src/stac_manager/modules/ingest.py`:

```python
"""Ingest Module - Fetch STAC Items from files or APIs."""
import json
import asyncio
from pathlib import Path
from typing import AsyncIterator

from stac_manager.modules.config import IngestConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import ConfigurationError


class IngestModule:
    """Fetches STAC Items from local files or remote APIs."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with configuration."""
        self.config = IngestConfig(**config)
        
        # Validate file exists for file mode
        if self.config.mode == "file":
            source_path = Path(self.config.source)
            if not source_path.exists():
                raise ConfigurationError(f"File not found: {self.config.source}")
    
    async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
        """
        Fetch items from configured source.
        
        Args:
            context: Workflow context
        
        Yields:
            STAC item dicts
        """
        if self.config.mode == "file":
            async for item in self._fetch_from_file():
                yield item
        else:
            async for item in self._fetch_from_api(context):
                yield item
    
    async def _fetch_from_file(self) -> AsyncIterator[dict]:
        """Fetch items from local file."""
        if self.config.format == "json":
            # Read JSON file
            source_path = Path(self.config.source)
            content = await asyncio.to_thread(source_path.read_text)
            items = json.loads(content)
            
            # Handle both FeatureCollection and list formats
            if isinstance(items, dict) and items.get("type") == "FeatureCollection":
                items = items.get("features", [])
            
            for item in items:
                yield item
        elif self.config.format == "parquet":
            # Parquet handling (Task 37)
            raise NotImplementedError("Parquet ingestion not yet implemented")
    
    async def _fetch_from_api(self, context: WorkflowContext) -> AsyncIterator[dict]:
        """Fetch items from STAC API."""
        # API mode implementation (Task 38)
        raise NotImplementedError("API ingestion not yet implemented")
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_ingest.py -v`  
Expected: All PASS

**Step 6: Update module exports**

Add to `src/stac_manager/modules/__init__.py`:

```python
from stac_manager.modules.ingest import IngestModule

__all__ = [
    # ... existing exports ...
    "IngestModule",
]
```

**Step 7: Commit**

```bash
git add src/stac_manager/modules/ingest.py tests/unit/modules/test_ingest.py src/stac_manager/modules/config.py src/stac_manager/modules/__init__.py
git commit -m "feat(modules): add IngestModule with JSON file support"
```

---

### Task 37: Ingest Module - File Mode (Parquet)

**Files:**
- Modify: `src/stac_manager/modules/ingest.py`
- Modify: `tests/unit/modules/test_ingest.py`

**Step 1: Write failing test for Parquet file ingestion**

Add to `tests/unit/modules/test_ingest.py`:

```python
import pyarrow as pa
import pyarrow.parquet as pq


@pytest.mark.asyncio
async def test_ingest_parquet_file_success(tmp_path):
    """IngestModule reads items from Parquet file."""
    # Create test Parquet file
    parquet_file = tmp_path / "items.parquet"
    test_items = [VALID_ITEM.copy(), {**VALID_ITEM, "id": "test-item-002"}]
    
    # Convert to Arrow Table
    table = pa.Table.from_pylist(test_items)
    pq.write_table(table, parquet_file)
    
    # Configure module
    config = {
        "mode": "file",
        "source": str(parquet_file),
        "format": "parquet"
    }
    module = IngestModule(config)
    context = MockWorkflowContext.create()
    
    # Fetch items
    results = [item async for item in module.fetch(context)]
    
    assert len(results) == 2
    assert results[0]["id"] == "test-item-001"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_ingest.py::test_ingest_parquet_file_success -v`  
Expected: FAIL with "NotImplementedError: Parquet ingestion not yet implemented"

**Step 3: Implement Parquet ingestion**

Update `_fetch_from_file` method in `src/stac_manager/modules/ingest.py`:

```python
    async def _fetch_from_file(self) -> AsyncIterator[dict]:
        """Fetch items from local file."""
        if self.config.format == "json":
            # Read JSON file
            source_path = Path(self.config.source)
            content = await asyncio.to_thread(source_path.read_text)
            items = json.loads(content)
            
            # Handle both FeatureCollection and list formats
            if isinstance(items, dict) and items.get("type") == "FeatureCollection":
                items = items.get("features", [])
            
            for item in items:
                yield item
                
        elif self.config.format == "parquet":
            # Read Parquet file
            import pyarrow.parquet as pq
            
            source_path = Path(self.config.source)
            # Use thread pool for blocking I/O
            table = await asyncio.to_thread(pq.read_table, str(source_path))
            
            # Convert to dicts and yield
            items = table.to_pylist()
            for item in items:
                yield item
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_ingest.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/ingest.py tests/unit/modules/test_ingest.py
git commit -m "feat(modules): add Parquet file support to IngestModule"
```

---

### Task 38: Ingest Module - API Mode (Basic Search)

**Files:**
- Modify: `src/stac_manager/modules/ingest.py`
- Modify: `tests/unit/modules/test_ingest.py`

**Step 1: Write failing test for API search**

Add to `tests/unit/modules/test_ingest.py`:

```python
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_ingest_api_search_success():
    """IngestModule fetches items from STAC API."""
    # Mock API client and search results
    mock_client = MagicMock()
    mock_search = MagicMock()
    
    # Mock items_as_dicts to return async iterator
    test_items = [VALID_ITEM.copy(), {**VALID_ITEM, "id": "test-item-002"}]
    
    async def mock_items_as_dicts():
        for item in test_items:
            yield item
    
    mock_search.items_as_dicts = mock_items_as_dicts
    mock_client.search.return_value = mock_search
    
    # Configure module for API mode
    config = {
        "mode": "api",
        "source": "https://example.com/stac",
        "collections": ["sentinel-2"],
        "limit": 100
    }
    
    with patch('pystac_client.Client.open', return_value=mock_client):
        module = IngestModule(config)
        context = MockWorkflowContext.create()
        
        # Fetch items
        results = [item async for item in module.fetch(context)]
    
    assert len(results) == 2
    assert results[0]["id"] == "test-item-001"
    assert results[1]["id"] == "test-item-002"
    
    # Verify search was called with correct params
    mock_client.search.assert_called_once()
    call_kwargs = mock_client.search.call_args.kwargs
    assert call_kwargs["collections"] == ["sentinel-2"]
    assert call_kwargs["limit"] == 100
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_ingest.py::test_ingest_api_search_success -v`  
Expected: FAIL with "NotImplementedError: API ingestion not yet implemented"

**Step 3: Implement API search functionality**

Update `_fetch_from_api` method in `src/stac_manager/modules/ingest.py`:

```python
    async def _fetch_from_api(self, context: WorkflowContext) -> AsyncIterator[dict]:
        """Fetch items from STAC API."""
        import pystac_client
        
        # Open STAC API client
        client = pystac_client.Client.open(self.config.source)
        
        # Build search parameters
        search_params = {
            "limit": self.config.limit,
        }
        
        if self.config.collections:
            search_params["collections"] = self.config.collections
        
        if self.config.max_items:
            search_params["max_items"] = self.config.max_items
        
        # Execute search
        search = client.search(**search_params)
        
        # Yield items as dicts
        async for item in search.items_as_dicts():
            yield item
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_ingest.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/ingest.py tests/unit/modules/test_ingest.py
git commit -m "feat(modules): add STAC API search to IngestModule"
```

---

### Task 39: Ingest Module - API Mode (Filters)

**Files:**
- Modify: `src/stac_manager/modules/ingest.py`
- Modify: `tests/unit/modules/test_ingest.py`

**Step 1: Write failing tests for filter parameters**

Add to `tests/unit/modules/test_ingest.py`:

```python
@pytest.mark.asyncio
async def test_ingest_api_filters_bbox():
    """IngestModule passes bbox filter to API search."""
    mock_client = MagicMock()
    mock_search = MagicMock()
    
    async def mock_items():
        return
        yield  # Make it an async generator
    
    mock_search.items_as_dicts = mock_items
    mock_client.search.return_value = mock_search
    
    config = {
        "mode": "api",
        "source": "https://example.com/stac",
        "bbox": [-180, -90, 180, 90]
    }
    
    with patch('pystac_client.Client.open', return_value=mock_client):
        module = IngestModule(config)
        context = MockWorkflowContext.create()
        _ = [item async for item in module.fetch(context)]
    
    call_kwargs = mock_client.search.call_args.kwargs
    assert call_kwargs["bbox"] == [-180, -90, 180, 90]


@pytest.mark.asyncio
async def test_ingest_api_filters_datetime():
    """IngestModule passes datetime filter to API search."""
    mock_client = MagicMock()
    mock_search = MagicMock()
    
    async def mock_items():
        return
        yield
    
    mock_search.items_as_dicts = mock_items
    mock_client.search.return_value = mock_search
    
    config = {
        "mode": "api",
        "source": "https://example.com/stac",
        "datetime": "2023-01-01/2023-12-31"
    }
    
    with patch('pystac_client.Client.open', return_value=mock_client):
        module = IngestModule(config)
        context = MockWorkflowContext.create()
        _ = [item async for item in module.fetch(context)]
    
    call_kwargs = mock_client.search.call_args.kwargs
    assert call_kwargs["datetime"] == "2023-01-01/2023-12-31"


@pytest.mark.asyncio
async def test_ingest_api_filters_query():
    """IngestModule passes CQL query filter to API search."""
    mock_client = MagicMock()
    mock_search = MagicMock()
    
    async def mock_items():
        return
        yield
    
    mock_search.items_as_dicts = mock_items
    mock_client.search.return_value = mock_search
    
    query_filter = {"eo:cloud_cover": {"lt": 10}}
    config = {
        "mode": "api",
        "source": "https://example.com/stac",
        "query": query_filter
    }
    
    with patch('pystac_client.Client.open', return_value=mock_client):
        module = IngestModule(config)
        context = MockWorkflowContext.create()
        _ = [item async for item in module.fetch(context)]
    
    call_kwargs = mock_client.search.call_args.kwargs
    assert call_kwargs["query"] == query_filter
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/modules/test_ingest.py::test_ingest_api_filters_bbox -v`  
Expected: FAIL - bbox not passed to search

**Step 3: Implement filter parameter mapping**

Update `_fetch_from_api` in `src/stac_manager/modules/ingest.py`:

```python
    async def _fetch_from_api(self, context: WorkflowContext) -> AsyncIterator[dict]:
        """Fetch items from STAC API."""
        import pystac_client
        
        # Open STAC API client
        client = pystac_client.Client.open(self.config.source)
        
        # Build search parameters
        search_params = {
            "limit": self.config.limit,
        }
        
        if self.config.collections:
            search_params["collections"] = self.config.collections
        
        if self.config.max_items:
            search_params["max_items"] = self.config.max_items
        
        # Add filter parameters
        if self.config.bbox:
            search_params["bbox"] = self.config.bbox
        
        if self.config.datetime:
            search_params["datetime"] = self.config.datetime
        
        if self.config.query:
            search_params["query"] = self.config.query
        
        # Execute search
        search = client.search(**search_params)
        
        # Yield items as dicts
        async for item in search.items_as_dicts():
            yield item
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_ingest.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/ingest.py tests/unit/modules/test_ingest.py
git commit -m "feat(modules): add bbox, datetime, query filters to IngestModule"
```

---

### Task 40: Ingest Module - Context Integration

**Files:**
- Modify: `src/stac_manager/modules/ingest.py`
- Modify: `tests/unit/modules/test_ingest.py`

**Note:** Temporal chunking and parallelism are deferred to Phase 3 (Orchestration) to maintain YAGNI principle. For Phase 2, we focus on basic fetching functionality.

**Step 1: Write failing test for context data override**

Add to `tests/unit/modules/test_ingest.py`:

```python
@pytest.mark.asyncio
async def test_ingest_context_override():
    """IngestModule uses context data to override config."""
    mock_client = MagicMock()
    mock_search = MagicMock()
    
    test_items = [VALID_ITEM.copy()]
    
    async def mock_items_as_dicts():
        for item in test_items:
            yield item
    
    mock_search.items_as_dicts = mock_items_as_dicts
    mock_client.search.return_value = mock_search
    
    # Config has default collection
    config = {
        "mode": "api",
        "source": "https://example.com/stac",
        "collections": ["default-collection"]
    }
    
    # Context overrides collection
    context = MockWorkflowContext.create(
        data={"collections": ["sentinel-1"]}
    )
    
    with patch('pystac_client.Client.open', return_value=mock_client):
        module = IngestModule(config)
        _ = [item async for item in module.fetch(context)]
    
    # Verify context override was used
    call_kwargs = mock_client.search.call_args.kwargs
    assert call_kwargs["collections"] == ["sentinel-1"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_ingest.py::test_ingest_context_override -v`  
Expected: FAIL - uses config collection instead of context

**Step 3: Implement context data merging**

Update `_fetch_from_api` in `src/stac_manager/modules/ingest.py`:

```python
    async def _fetch_from_api(self, context: WorkflowContext) -> AsyncIterator[dict]:
        """Fetch items from STAC API."""
        import pystac_client
        
        # Open STAC API client
        client = pystac_client.Client.open(self.config.source)
        
        # Build search parameters with context overrides
        search_params = {
            "limit": self.config.limit,
        }
        
        # Use context data if available, otherwise use config
        collections = context.data.get("collections", self.config.collections)
        if collections:
            search_params["collections"] = collections
        
        bbox = context.data.get("bbox", self.config.bbox)
        if bbox:
            search_params["bbox"] = bbox
        
        datetime_val = context.data.get("datetime", self.config.datetime)
        if datetime_val:
            search_params["datetime"] = datetime_val
        
        if self.config.max_items:
            search_params["max_items"] = self.config.max_items
        
        if self.config.query:
            search_params["query"] = self.config.query
        
        # Execute search
        search = client.search(**search_params)
        
        # Yield items as dicts
        async for item in search.items_as_dicts():
            yield item
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_ingest.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/ingest.py tests/unit/modules/test_ingest.py
git commit -m "feat(modules): add context data override to IngestModule"
```

---

### Task 41: Ingest Module - Error Handling

**Files:**
- Modify: `src/stac_manager/modules/ingest.py`
- Modify: `src/stac_manager/modules/config.py`
- Modify: `tests/unit/modules/test_ingest.py`

**Step 1: Write failing test for API error handling**

Add to `tests/unit/modules/test_ingest.py`:

```python
from pystac_client.exceptions import APIError


@pytest.mark.asyncio
async def test_ingest_api_error_strict_mode():
    """IngestModule raises error in strict mode on API failure."""
    mock_client = MagicMock()
    mock_client.search.side_effect = APIError("API Error")
    
    config = {
        "mode": "api",
        "source": "https://example.com/stac",
        "strict": True
    }
    
    with patch('pystac_client.Client.open', return_value=mock_client):
        module = IngestModule(config)
        context = MockWorkflowContext.create()
        
        from stac_manager.exceptions import DataProcessingError
        with pytest.raises(DataProcessingError, match="API Error"):
            _ = [item async for item in module.fetch(context)]


@pytest.mark.asyncio
async def test_ingest_api_error_permissive_mode():
    """IngestModule logs error in permissive mode and continues."""
    mock_client = MagicMock()
    mock_search = MagicMock()
    
    # First call fails, second succeeds
    call_count = 0
    
    async def mock_items_as_dicts():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise APIError("Temporary failure")
        yield VALID_ITEM.copy()
    
    mock_search.items_as_dicts = mock_items_as_dicts
    mock_client.search.return_value = mock_search
    
    config = {
        "mode": "api",
        "source": "https://example.com/stac",
        "strict": False
    }
    
    with patch('pystac_client.Client.open', return_value=mock_client):
        module = IngestModule(config)
        context = MockWorkflowContext.create()
        
        try:
            results = [item async for item in module.fetch(context)]
        except APIError:
            pass  # Expected in permissive mode
    
    # Verify error was logged
    assert len(context.failure_collector.failures) >= 1
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_ingest.py::test_ingest_api_error_strict_mode -v`  
Expected: FAIL - APIError not caught and re-raised

**Step 3: Add strict config option**

Update `IngestConfig` in `src/stac_manager/modules/config.py`:

```python
class IngestConfig(BaseModel):
    """Configuration for IngestModule."""
    mode: Literal["file", "api"] = Field(description="Ingestion mode")
    source: str = Field(description="File path or API URL")
    format: Optional[Literal["json", "parquet"]] = Field(default="json", description="File format (file mode only)")
    collections: Optional[list[str]] = Field(default=None, description="Collections to search (API mode)")
    bbox: Optional[list[float]] = Field(default=None, description="Bounding box filter")
    datetime: Optional[str] = Field(default=None, description="Datetime filter")
    query: Optional[dict] = Field(default=None, description="CQL query")
    limit: Optional[int] = Field(default=100, description="Items per page")
    max_items: Optional[int] = Field(default=None, description="Maximum items to fetch")
    strict: bool = Field(default=True, description="Fail on errors (True) or log and continue (False)")
```

**Step 4: Implement error handling**

Update `_fetch_from_api` in `src/stac_manager/modules/ingest.py`:

```python
    async def _fetch_from_api(self, context: WorkflowContext) -> AsyncIterator[dict]:
        """Fetch items from STAC API."""
        import pystac_client
        from pystac_client.exceptions import APIError
        from stac_manager.exceptions import DataProcessingError
        
        try:
            # Open STAC API client
            client = pystac_client.Client.open(self.config.source)
            
            # Build search parameters with context overrides
            search_params = {
                "limit": self.config.limit,
            }
            
            # Use context data if available, otherwise use config
            collections = context.data.get("collections", self.config.collections)
            if collections:
                search_params["collections"] = collections
            
            bbox = context.data.get("bbox", self.config.bbox)
            if bbox:
                search_params["bbox"] = bbox
            
            datetime_val = context.data.get("datetime", self.config.datetime)
            if datetime_val:
                search_params["datetime"] = datetime_val
            
            if self.config.max_items:
                search_params["max_items"] = self.config.max_items
            
            if self.config.query:
                search_params["query"] = self.config.query
            
            # Execute search
            search = client.search(**search_params)
            
            # Yield items as dicts
            async for item in search.items_as_dicts():
                yield item
                
        except APIError as e:
            error_msg = f"STAC API error: {str(e)}"
            
            if self.config.strict:
                raise DataProcessingError(error_msg) from e
            else:
                # Log error and continue
                context.failure_collector.add(
                    item_id="unknown",
                    error=error_msg,
                    step_id="ingest"
                )
                context.logger.warning(f"API error in permissive mode: {error_msg}")
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_ingest.py -v`  
Expected: All PASS

**Step 6: Commit**

```bash
git add src/stac_manager/modules/ingest.py src/stac_manager/modules/config.py tests/unit/modules/test_ingest.py
git commit -m "feat(modules): add error handling with strict/permissive modes to IngestModule"
```

---

### Task 42: Ingest Module - Protocol Compliance

**Files:**
- Modify: `tests/unit/modules/test_ingest.py`

**Step 1: Write failing test for Fetcher protocol compliance**

Add to `tests/unit/modules/test_ingest.py`:

```python
from stac_manager.protocols import Fetcher


def test_ingest_protocol_compliance():
    """IngestModule implements Fetcher protocol."""
    config = {
        "mode": "file",
        "source": "/tmp/items.json",
        "format": "json"
    }
    
    # Note: This will fail initially due to file not existing
    # Use a valid temp file for the test
    import tempfile
    import json
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([VALID_ITEM.copy()], f)
        temp_file = f.name
    
    try:
        config["source"] = temp_file
        module = IngestModule(config)
        
        # Check protocol compliance
        assert isinstance(module, Fetcher)
        assert hasattr(module, 'fetch')
        assert callable(module.fetch)
    finally:
        import os
        os.unlink(temp_file)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_ingest.py::test_ingest_protocol_compliance -v`  
Expected: FAIL with "AssertionError: assert False" (protocol not implemented)

**Step 3: Verify fetch signature matches protocol**

The `fetch` method already has the correct signature: `async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]`

Protocol compliance should now pass automatically since the signature matches.

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_ingest.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add tests/unit/modules/test_ingest.py
git commit -m "test(modules): add Fetcher protocol compliance test for IngestModule"
```

---

## Phase 8: Output Module

### Task 45: Output Module - JSON Writer (Basic)

**Files:**
- Create: `src/stac_manager/modules/output.py`
- Create: `tests/unit/modules/test_output.py`
- Modify: `src/stac_manager/modules/__init__.py`
- Modify: `src/stac_manager/modules/config.py`

**Step 1: Write failing test for basic JSON output**

Create `tests/unit/modules/test_output.py`:

```python
import pytest
import json
from pathlib import Path
from tests.fixtures.context import MockWorkflowContext
from tests.fixtures.stac_items import VALID_ITEM
from stac_manager.modules.output import OutputModule


@pytest.mark.asyncio
async def test_output_json_basic(tmp_path):
    """OutputModule writes items as JSON files."""
    config = {
        "format": "json",
        "base_dir": str(tmp_path)
    }
    
    module = OutputModule(config)
    context = MockWorkflowContext.create()
    
    # Bundle item
    item = VALID_ITEM.copy()
    await module.bundle(item, context)
    
    # Finalize
    result = await module.finalize(context)
    
    # Verify file exists
    item_file = tmp_path / f"{item['id']}.json"
    assert item_file.exists()
    
    # Verify content
    content = json.loads(item_file.read_text())
    assert content["id"] == item["id"]
    assert content["type"] == "Feature"
    
    # Verify result manifest
    assert result["items_written"] == 1


@pytest.mark.asyncio
async def test_output_creates_directory(tmp_path):
    """OutputModule creates output directory if missing."""
    output_dir = tmp_path / "nested" / "output"
    
    config = {
        "format": "json",
        "base_dir": str(output_dir)
    }
    
    module = OutputModule(config)
    context = MockWorkflowContext.create()
    
    await module.bundle(VALID_ITEM.copy(), context)
    await module.finalize(context)
    
    assert output_dir.exists()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_output.py::test_output_json_basic -v`  
Expected: FAIL with "ModuleNotFoundError: No module named 'stac_manager.modules.output'"

**Step 3: Create OutputConfig model**

Add to `src/stac_manager/modules/config.py`:

```python
class OutputConfig(BaseModel):
    """Configuration for OutputModule."""
    format: Literal["json", "parquet"] = Field(description="Output format")
    base_dir: str = Field(description="Base output directory")
    buffer_size: int = Field(default=1000, description="Items to buffer before flushing")
    base_url: Optional[str] = Field(default=None, description="Base URL for item links")
    include_collection: bool = Field(default=False, description="Write collection.json")
```

**Step 4: Implement basic OutputModule**

Create `src/stac_manager/modules/output.py`:

```python
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
        Add item to output buffer.
        
        Args:
            item: STAC item dict
            context: Workflow context
        """
        self.buffer.append(item)
        
        # Flush if buffer is full
        if len(self.buffer) >= self.config.buffer_size:
            await self._flush(context)
    
    async def finalize(self, context: WorkflowContext) -> dict:
        """
        Flush remaining items and return manifest.
        
        Args:
            context: Workflow context
        
        Returns:
            Output result manifest
        """
        # Flush any remaining items
        if self.buffer:
            await self._flush(context)
        
        return {
            "items_written": self.items_written,
            "format": self.config.format,
            "output_dir": self.config.base_dir
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
        """Write items as individual JSON files."""
        output_dir = Path(self.config.base_dir)
        
        # Create directory if missing
        await asyncio.to_thread(output_dir.mkdir, parents=True, exist_ok=True)
        
        # Write each item
        for item in self.buffer:
            item_id = item.get("id", "unknown")
            item_path = output_dir / f"{item_id}.json"
            
            # Write JSON
            content = json.dumps(item, indent=2)
            await asyncio.to_thread(item_path.write_text, content)
            
            self.items_written += 1
        
        # Clear buffer
        self.buffer.clear()
    
    async def _flush_parquet(self, context: WorkflowContext) -> None:
        """Write items as Parquet file."""
        # Parquet implementation (Task 48)
        raise NotImplementedError("Parquet output not yet implemented")
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_output.py -v`  
Expected: All PASS

**Step 6: Update module exports**

Add to `src/stac_manager/modules/__init__.py`:

```python
from stac_manager.modules.output import OutputModule

__all__ = [
    # ... existing exports ...
    "OutputModule",
]
```

**Step 7: Commit**

```bash
git add src/stac_manager/modules/output.py tests/unit/modules/test_output.py src/stac_manager/modules/config.py src/stac_manager/modules/__init__.py
git commit -m "feat(modules): add OutputModule with JSON file support"
```

---

### Task 46: Output Module - Atomic Writes

**Files:**
- Modify: `src/stac_manager/modules/output.py`
- Modify: `tests/unit/modules/test_output.py`

**Step 1: Write failing test for atomic writes**

Add to `tests/unit/modules/test_output.py`:

```python
from unittest.mock import patch, MagicMock
import os


@pytest.mark.asyncio
async def test_output_atomic_write(tmp_path):
    """OutputModule uses atomic writes (temp file + rename)."""
    config = {
        "format": "json",
        "base_dir": str(tmp_path)
    }
    
    module = OutputModule(config)
    context = MockWorkflowContext.create()
    
    item = VALID_ITEM.copy()
    
    # Track file operations
    write_calls = []
    rename_calls = []
    
    original_write = Path.write_text
    original_replace = os.replace
    
    def track_write(self, content, *args, **kwargs):
        write_calls.append(str(self))
        return original_write(self, content, *args, **kwargs)
    
    def track_replace(src, dst):
        rename_calls.append((src, dst))
        return original_replace(src, dst)
    
    with patch.object(Path, 'write_text', track_write):
        with patch('os.replace', track_replace):
            await module.bundle(item, context)
            await module.finalize(context)
    
    # Verify atomic pattern: write to .tmp then rename
    assert len(write_calls) == 1
    assert write_calls[0].endswith('.tmp')
    
    assert len(rename_calls) == 1
    src, dst = rename_calls[0]
    assert src.endswith('.tmp')
    assert dst.endswith('.json')
    assert not dst.endswith('.tmp.json')
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_output.py::test_output_atomic_write -v`  
Expected: FAIL - writes directly without temp file

**Step 3: Implement atomic write pattern**

Update `_flush_json` in `src/stac_manager/modules/output.py`:

```python
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
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_output.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/output.py tests/unit/modules/test_output.py
git commit -m "feat(modules): add atomic writes to OutputModule"
```

---

### Task 47: Output Module - Buffering Strategy

**Files:**
- Modify: `tests/unit/modules/test_output.py`

**Step 1: Write test for buffering behavior**

Add to `tests/unit/modules/test_output.py`:

```python
@pytest.mark.asyncio
async def test_output_buffering(tmp_path):
    """OutputModule buffers items and flushes at threshold."""
    config = {
        "format": "json",
        "base_dir": str(tmp_path),
        "buffer_size": 3  # Small buffer for testing
    }
    
    module = OutputModule(config)
    context = MockWorkflowContext.create()
    
    # Add 2 items - should not write yet
    await module.bundle({**VALID_ITEM, "id": "item-1"}, context)
    await module.bundle({**VALID_ITEM, "id": "item-2"}, context)
    
    assert len(list(tmp_path.glob("*.json"))) == 0
    
    # Add 3rd item - should trigger flush
    await module.bundle({**VALID_ITEM, "id": "item-3"}, context)
    
    assert len(list(tmp_path.glob("*.json"))) == 3
    
    # Add 2 more items - should not write yet
    await module.bundle({**VALID_ITEM, "id": "item-4"}, context)
    await module.bundle({**VALID_ITEM, "id": "item-5"}, context)
    
    assert len(list(tmp_path.glob("*.json"))) == 3
    
    # Finalize - should flush remaining
    await module.finalize(context)
    
    assert len(list(tmp_path.glob("*.json"))) == 5
```

**Step 2: Run test to verify behavior**

Run: `pytest tests/unit/modules/test_output.py::test_output_buffering -v`  
Expected: PASS (buffering already implemented in Task 45)

**Step 3: Commit**

```bash
git add tests/unit/modules/test_output.py
git commit -m "test(modules): add buffering behavior test for OutputModule"
```

---

### Task 48: Output Module - Parquet Writer

**Files:**
- Modify: `src/stac_manager/modules/output.py`
- Modify: `tests/unit/modules/test_output.py`

**Step 1: Write failing test for Parquet output**

Add to `tests/unit/modules/test_output.py`:

```python
import pyarrow.parquet as pq


@pytest.mark.asyncio
async def test_output_parquet(tmp_path):
    """OutputModule writes items as Parquet file."""
    config = {
        "format": "parquet",
        "base_dir": str(tmp_path),
        "buffer_size": 10
    }
    
    module = OutputModule(config)
    context = MockWorkflowContext.create()
    
    # Bundle multiple items
    items = [
        {**VALID_ITEM, "id": f"item-{i}"}
        for i in range(5)
    ]
    
    for item in items:
        await module.bundle(item, context)
    
    # Finalize
    result = await module.finalize(context)
    
    # Verify Parquet file exists
    parquet_files = list(tmp_path.glob("*.parquet"))
    assert len(parquet_files) == 1
    
    # Verify content
    table = pq.read_table(str(parquet_files[0]))
    assert len(table) == 5
    
    # Verify result
    assert result["items_written"] == 5
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_output.py::test_output_parquet -v`  
Expected: FAIL with "NotImplementedError: Parquet output not yet implemented"

**Step 3: Implement Parquet output**

Update `_flush_parquet` in `src/stac_manager/modules/output.py`:

```python
    async def _flush_parquet(self, context: WorkflowContext) -> None:
        """Write items as Parquet file."""
        import pyarrow as pa
        import pyarrow.parquet as pq
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
            import os
            await asyncio.to_thread(os.replace, str(temp_path), str(parquet_path))
            
            self.items_written += len(self.buffer)
            
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                await asyncio.to_thread(temp_path.unlink)
            raise
        
        # Clear buffer
        self.buffer.clear()
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_output.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/output.py tests/unit/modules/test_output.py
git commit -m "feat(modules): add Parquet output to OutputModule"
```

---

### Task 49: Output Module - Link Management

**Files:**
- Modify: `src/stac_manager/modules/output.py`
- Modify: `src/stac_manager/modules/config.py`
- Modify: `tests/unit/modules/test_output.py`

**Step 1: Write failing test for link updates**

Add to `tests/unit/modules/test_output.py`:

```python
@pytest.mark.asyncio
async def test_output_link_updates(tmp_path):
    """OutputModule updates self links in output items."""
    config = {
        "format": "json",
        "base_dir": str(tmp_path),
        "base_url": "https://new-catalog.com/items"
    }
    
    module = OutputModule(config)
    context = MockWorkflowContext.create()
    
    # Item with old self link
    item = {
        **VALID_ITEM,
        "links": [
            {"rel": "self", "href": "https://old-catalog.com/item-001.json"},
            {"rel": "parent", "href": "https://old-catalog.com/collection.json"}
        ]
    }
    
    await module.bundle(item, context)
    await module.finalize(context)
    
    # Read written item
    item_file = tmp_path / "test-item-001.json"
    written_item = json.loads(item_file.read_text())
    
    # Verify self link updated
    self_link = next(l for l in written_item["links"] if l["rel"] == "self")
    assert self_link["href"] == "https://new-catalog.com/items/test-item-001.json"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_output.py::test_output_link_updates -v`  
Expected: FAIL - links not updated

**Step 3: Implement link management**

Add helper method to `src/stac_manager/modules/output.py`:

```python
    def _update_links(self, item: dict) -> dict:
        """Update item links to match output location."""
        if not self.config.base_url:
            return item
        
        # Create copy to avoid modifying original
        item = item.copy()
        
        item_id = item.get("id", "unknown")
        
        # Update self link
        if "links" in item:
            for link in item["links"]:
                if link.get("rel") == "self":
                    # Update to new location
                    if self.config.format == "json":
                        link["href"] = f"{self.config.base_url}/{item_id}.json"
                    elif self.config.format == "parquet":
                        # For parquet, self link points to the parquet file
                        link["href"] = f"{self.config.base_url}/items.parquet"
        
        return item
```

Update `bundle` method to use link updates:

```python
    async def bundle(self, item: dict, context: WorkflowContext) -> None:
        """
        Add item to output buffer.
        
        Args:
            item: STAC item dict
            context: Workflow context
        """
        # Update links if base_url configured
        item = self._update_links(item)
        
        self.buffer.append(item)
        
        # Flush if buffer is full
        if len(self.buffer) >= self.config.buffer_size:
            await self._flush(context)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_output.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/output.py tests/unit/modules/test_output.py
git commit -m "feat(modules): add link management to OutputModule"
```

---

### Task 50: Output Module - Collection File Generation

**Files:**
- Modify: `src/stac_manager/modules/output.py`
- Modify: `tests/unit/modules/test_output.py`

**Step 1: Write failing test for collection output**

Add to `tests/unit/modules/test_output.py`:

```python
@pytest.mark.asyncio
async def test_output_collection_file(tmp_path):
    """OutputModule writes collection.json if configured."""
    config = {
        "format": "json",
        "base_dir": str(tmp_path),
        "include_collection": True
    }
    
    module = OutputModule(config)
    
    # Context with collection
    collection = {
        "id": "test-collection",
        "type": "Collection",
        "stac_version": "1.0.0",
        "description": "Test collection",
        "license": "proprietary",
        "extent": {
            "spatial": {"bbox": [[-180, -90, 180, 90]]},
            "temporal": {"interval": [[None, None]]}
        },
        "links": []
    }
    
    context = MockWorkflowContext.create(data={"collection": collection})
    
    # Bundle item
    await module.bundle(VALID_ITEM.copy(), context)
    await module.finalize(context)
    
    # Verify collection file exists
    collection_file = tmp_path / "collection.json"
    assert collection_file.exists()
    
    # Verify content
    written_collection = json.loads(collection_file.read_text())
    assert written_collection["id"] == "test-collection"
    assert written_collection["type"] == "Collection"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_output.py::test_output_collection_file -v`  
Expected: FAIL - collection.json not created

**Step 3: Implement collection file generation**

Update `finalize` method in `src/stac_manager/modules/output.py`:

```python
    async def finalize(self, context: WorkflowContext) -> dict:
        """
        Flush remaining items and return manifest.
        
        Args:
            context: Workflow context
        
        Returns:
            Output result manifest
        """
        # Flush any remaining items
        if self.buffer:
            await self._flush(context)
        
        # Write collection if configured
        if self.config.include_collection:
            await self._write_collection(context)
        
        return {
            "items_written": self.items_written,
            "format": self.config.format,
            "output_dir": self.config.base_dir
        }
    
    async def _write_collection(self, context: WorkflowContext) -> None:
        """Write collection.json to output directory."""
        import os
        
        collection = context.data.get("collection")
        if not collection:
            context.logger.warning("include_collection=True but no collection in context")
            return
        
        output_dir = Path(self.config.base_dir)
        collection_path = output_dir / "collection.json"
        temp_path = output_dir / "collection.json.tmp"
        
        try:
            # Write to temp file
            content = json.dumps(collection, indent=2)
            await asyncio.to_thread(temp_path.write_text, content)
            
            # Atomic rename
            await asyncio.to_thread(os.replace, str(temp_path), str(collection_path))
            
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                await asyncio.to_thread(temp_path.unlink)
            raise
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_output.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/output.py tests/unit/modules/test_output.py
git commit -m "feat(modules): add collection.json generation to OutputModule"
```

---

### Task 51: Output Module - Protocol Compliance

**Files:**
- Modify: `tests/unit/modules/test_output.py`

**Step 1: Write failing test for Bundler protocol compliance**

Add to `tests/unit/modules/test_output.py`:

```python
from stac_manager.protocols import Bundler


def test_output_protocol_compliance(tmp_path):
    """OutputModule implements Bundler protocol."""
    config = {
        "format": "json",
        "base_dir": str(tmp_path)
    }
    
    module = OutputModule(config)
    
    # Check protocol compliance
    assert isinstance(module, Bundler)
    assert hasattr(module, 'bundle')
    assert callable(module.bundle)
    assert hasattr(module, 'finalize')
    assert callable(module.finalize)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_output.py::test_output_protocol_compliance -v`  
Expected: FAIL with "AssertionError: assert False"

**Step 3: Verify method signatures match protocol**

The `bundle` and `finalize` methods already have correct signatures:
- `async def bundle(self, item: dict, context: WorkflowContext) -> None`
- `async def finalize(self, context: WorkflowContext) -> dict`

Protocol compliance should now pass.

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_output.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add tests/unit/modules/test_output.py
git commit -m "test(modules): add Bundler protocol compliance test for OutputModule"
```

---

## Phase 9: Integration & Verification

### Task 52: Integration Test - Seed → Update → Output

**Files:**
- Create: `tests/integration/test_pipeline_e2e.py`

**Step 1: Write failing test for simple pipeline**

Create `tests/integration/test_pipeline_e2e.py`:

```python
"""End-to-end integration tests for module pipelines."""

import pytest
import json
from pathlib import Path

from stac_manager.core.context import WorkflowContext
from stac_manager.modules.seed import SeedModule
from stac_manager.modules.update import UpdateModule
from stac_manager.modules.output import OutputModule


@pytest.mark.asyncio
async def test_seed_update_output_pipeline(tmp_path):
    """Simple pipeline: Seed → Update → Output."""
    
    # Create input item file
    input_file = tmp_path / "input.json"
    seed_item = {
        "type": "Feature",
        "stac_version": "1.0.0",
        "id": "test-item-001",
        "geometry": {
            "type": "Point",
            "coordinates": [0, 0]
        },
        "bbox": [0, 0, 0, 0],
        "properties": {
            "datetime": "2024-01-01T00:00:00Z",
            "title": "Original Title"
        },
        "links": [],
        "assets": {}
    }
    
    input_file.write_text(json.dumps({"type": "FeatureCollection", "features": [seed_item]}))
    
    # Output directory
    output_dir = tmp_path / "output"
    
    # Initialize modules
    seed_config = {"mode": "file", "source": str(input_file), "format": "json"}
    update_config = {"operations": [{"type": "set_property", "key": "title", "value": "Updated Title"}]}
    output_config = {"format": "json", "base_dir": str(output_dir)}
    
    seed = SeedModule(seed_config)
    update = UpdateModule(update_config)
    output = OutputModule(output_config)
    
    # Create context
    context = WorkflowContext.create()
    
    # Execute pipeline
    # Phase 1: Fetch items
    items = []
    async for item in seed.fetch(context):
        items.append(item)
    
    assert len(items) == 1
    assert items[0]["properties"]["title"] == "Original Title"
    
    # Phase 2: Transform items
    transformed = []
    for item in items:
        modified_item = await update.modify(item, context)
        transformed.append(modified_item)
    
    assert transformed[0]["properties"]["title"] == "Updated Title"
    
    # Phase 3: Bundle output
    for item in transformed:
        await output.bundle(item, context)
    
    result = await output.finalize(context)
    
    # Verify output
    assert result["items_written"] == 1
    
    output_file = output_dir / "test-item-001.json"
    assert output_file.exists()
    
    written_item = json.loads(output_file.read_text())
    assert written_item["properties"]["title"] == "Updated Title"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_pipeline_e2e.py::test_seed_update_output_pipeline -v`  
Expected: FAIL if modules not yet integrated correctly

**Step 3: Verify integration**

If test fails, check:
- SeedModule `fetch()` generator working
- UpdateModule `modify()` returns transformed item
- OutputModule `bundle()` accepts items

All implementations should already be complete from prior tasks.

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_pipeline_e2e.py -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/integration/test_pipeline_e2e.py
git commit -m "test(integration): add simple Seed→Update→Output pipeline test"
```

---

### Task 53: Integration Test - Ingest → Transform → Validate → Output

**Files:**
- Modify: `tests/integration/test_pipeline_e2e.py`

**Step 1: Write failing test for complex multi-module pipeline**

Add to `tests/integration/test_pipeline_e2e.py`:

```python
from stac_manager.modules.ingest import IngestModule
from stac_manager.modules.transform import TransformModule
from stac_manager.modules.validate import ValidateModule
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_complex_pipeline(tmp_path):
    """Complex pipeline: Ingest → Transform → Validate → Output."""
    
    # Mock STAC API response
    mock_items = [
        {
            "type": "Feature",
            "stac_version": "1.0.0",
            "id": f"api-item-{i:03d}",
            "geometry": {"type": "Point", "coordinates": [i, i]},
            "bbox": [i, i, i, i],
            "properties": {
                "datetime": "2024-01-01T00:00:00Z",
                "eo:cloud_cover": 50.0
            },
            "links": [],
            "assets": {}
        }
        for i in range(10)
    ]
    
    output_dir = tmp_path / "output"
    
    # Module configs
    ingest_config = {
        "mode": "api",
        "source": "https://fake-stac.example.com",
        "max_items": 10
    }
    
    transform_config = {
        "operations": [
            {"type": "set_property", "key": "processing:level", "value": "L2A"}
        ]
    }
    
    validate_config = {
        "schema_version": "1.0.0",
        "strict": False
    }
    
    output_config = {
        "format": "json",
        "base_dir": str(output_dir),
        "base_url": "https://output-catalog.com/items"
    }
    
    # Initialize modules
    ingest = IngestModule(ingest_config)
    transform = TransformModule(transform_config)
    validate = ValidateModule(validate_config)
    output = OutputModule(output_config)
    
    context = WorkflowContext.create()
    
    # Mock API client
    with patch("pystac_client.Client.open") as mock_open:
        mock_client = AsyncMock()
        mock_search = AsyncMock()
        mock_search.items_as_dicts.return_value = iter(mock_items)
        mock_client.search.return_value = mock_search
        mock_open.return_value = mock_client
        
        # Execute pipeline
        # Phase 1: Ingest from API
        items = []
        async for item in ingest.fetch(context):
            items.append(item)
        
        assert len(items) == 10
        
        # Phase 2: Transform
        transformed = []
        for item in items:
            modified = await transform.modify(item, context)
            transformed.append(modified)
        
        assert all(
            item["properties"]["processing:level"] == "L2A"
            for item in transformed
        )
        
        # Phase 3: Validate
        validated = []
        for item in transformed:
            # Validate returns item if valid, logs failures
            valid_item = await validate.modify(item, context)
            if valid_item:  # None if validation failed
                validated.append(valid_item)
        
        assert len(validated) == 10  # All should pass
        
        # Phase 4: Bundle output
        for item in validated:
            await output.bundle(item, context)
        
        result = await output.finalize(context)
        
        # Verify results
        assert result["items_written"] == 10
        
        # Check output files
        output_files = list(output_dir.glob("*.json"))
        assert len(output_files) == 10
        
        # Verify link updates
        sample_file = output_dir / "api-item-000.json"
        sample_item = json.loads(sample_file.read_text())
        
        self_link = next(l for l in sample_item["links"] if l["rel"] == "self")
        assert self_link["href"].startswith("https://output-catalog.com/items/")
```

**Step 2: Run test to verify behavior**

Run: `pytest tests/integration/test_pipeline_e2e.py::test_complex_pipeline -v`  
Expected: PASS (all modules integrated)

**Step 3: Add assertions for failure collection**

This test validates happy path. Next task covers failure scenarios.

**Step 4: Commit**

```bash
git add tests/integration/test_pipeline_e2e.py
git commit -m "test(integration): add complex multi-module pipeline test"
```

---

### Task 54: Integration Test - Failure Collection

**Files:**
- Modify: `tests/integration/test_pipeline_e2e.py`

**Step 1: Write failing test for failure propagation**

Add to `tests/integration/test_pipeline_e2e.py`:

```python
@pytest.mark.asyncio
async def test_pipeline_failure_collection(tmp_path):
    """Pipeline collects failures across modules."""
    
    # Create input with mix of valid/invalid items
    input_file = tmp_path / "input.json"
    
    items = [
        # Valid item
        {
            "type": "Feature",
            "stac_version": "1.0.0",
            "id": "valid-item",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
            "bbox": [0, 0, 0, 0],
            "properties": {"datetime": "2024-01-01T00:00:00Z"},
            "links": [],
            "assets": {}
        },
        # Invalid item - missing geometry
        {
            "type": "Feature",
            "stac_version": "1.0.0",
            "id": "invalid-no-geometry",
            "properties": {"datetime": "2024-01-01T00:00:00Z"},
            "links": [],
            "assets": {}
        },
        # Another valid item
        {
            "type": "Feature",
            "stac_version": "1.0.0",
            "id": "valid-item-2",
            "geometry": {"type": "Point", "coordinates": [1, 1]},
            "bbox": [1, 1, 1, 1],
            "properties": {"datetime": "2024-01-02T00:00:00Z"},
            "links": [],
            "assets": {}
        }
    ]
    
    input_file.write_text(json.dumps({"type": "FeatureCollection", "features": items}))
    
    output_dir = tmp_path / "output"
    
    # Configure modules
    seed_config = {"mode": "file", "source": str(input_file), "format": "json"}
    validate_config = {"schema_version": "1.0.0", "strict": False}  # Permissive mode
    output_config = {"format": "json", "base_dir": str(output_dir)}
    
    seed = SeedModule(seed_config)
    validate = ValidateModule(validate_config)
    output = OutputModule(output_config)
    
    context = WorkflowContext.create()
    
    # Execute pipeline
    fetched = []
    async for item in seed.fetch(context):
        fetched.append(item)
    
    assert len(fetched) == 3
    
    # Validate - should log failure for invalid item
    validated = []
    for item in fetched:
        result = await validate.modify(item, context)
        if result:  # None if validation failed
            validated.append(result)
    
    # Should have 2 valid, 1 failure logged
    assert len(validated) == 2
    
    # Check failures
    failures = context.get_failures()
    assert len(failures) == 1
    assert failures[0]["item_id"] == "invalid-no-geometry"
    assert "geometry" in failures[0]["error"].lower()
    
    # Output only valid items
    for item in validated:
        await output.bundle(item, context)
    
    result = await output.finalize(context)
    
    assert result["items_written"] == 2
    
    # Verify output files
    output_files = list(output_dir.glob("*.json"))
    assert len(output_files) == 2
    assert (output_dir / "valid-item.json").exists()
    assert (output_dir / "valid-item-2.json").exists()
    assert not (output_dir / "invalid-no-geometry.json").exists()
```

**Step 2: Run test to verify failure handling**

Run: `pytest tests/integration/test_pipeline_e2e.py::test_pipeline_failure_collection -v`  
Expected: PASS - failures collected, valid items processed

**Step 3: Add failure summary assertion**

This test confirms:
- Invalid items logged to `FailureCollector`
- Valid items continue through pipeline
- Output only contains validated items
- Failures accessible via `context.get_failures()`

**Step 4: Run all integration tests**

Run: `pytest tests/integration/ -v --tb=short`  
Expected: All PASS

**Step 5: Commit**

```bash
git add tests/integration/test_pipeline_e2e.py
git commit -m "test(integration): add failure collection across pipeline modules"
```

---

### Task 55: Module Documentation

**Files:**
- Create: `src/stac_manager/modules/README.md`

**Step 1: Create module documentation outline**

Create `src/stac_manager/modules/README.md`:

```markdown
# STAC Manager Pipeline Modules

This directory contains all pipeline module implementations for the STAC Manager library.

## Module Types

Pipeline modules implement three core protocols:

- **Fetcher**: Produces items from external sources (APIs, files)
- **Modifier**: Transforms items in-place (1-to-1)
- **Bundler**: Collects and writes items to output destinations

## Available Modules

### Fetcher Modules

#### SeedModule

Generate synthetic STAC items for testing and prototyping.

**Config Options**:
```python
{
    "items": [
        {
            "id": "test-item-001",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
            "properties": {"datetime": "2024-01-01T00:00:00Z"}
        }
    ]
}
```

**Usage**:
```python
from stac_manager.modules.seed import SeedModule
from stac_manager.core.context import WorkflowContext

module = SeedModule({"items": [...]})
context = WorkflowContext.create()

async for item in module.fetch(context):
    print(item["id"])
```

#### IngestModule

Fetch STAC items from files or STAC APIs.

**Config Options**:
```python
{
    "mode": "file",  # or "api"
    "source": "/path/to/items.json",  # file path or API URL
    "format": "json",  # or "parquet" (file mode only)
    "max_items": 100,  # optional limit
    "filters": {  # API mode only
        "bbox": [-180, -90, 180, 90],
        "datetime": "2024-01-01/2024-12-31",
        "query": {"eo:cloud_cover": {"lt": 10}}
    },
    "strict": True  # raise on errors vs log to FailureCollector
}
```

**File Mode Usage**:
```python
from stac_manager.modules.ingest import IngestModule

# JSON FeatureCollection
module = IngestModule({
    "mode": "file",
    "source": "items.json",
    "format": "json"
})

# Parquet
module = IngestModule({
    "mode": "file",
    "source": "items.parquet",
    "format": "parquet"
})

async for item in module.fetch(context):
    process(item)
```

**API Mode Usage**:
```python
# Search with filters
module = IngestModule({
    "mode": "api",
    "source": "https://earth-search.aws.element84.com/v1",
    "max_items": 50,
    "filters": {
        "collections": ["sentinel-2-l2a"],
        "bbox": [-122.5, 37.7, -122.3, 37.9],
        "datetime": "2024-01-01/2024-01-31"
    }
})

async for item in module.fetch(context):
    process(item)
```

### Modifier Modules

#### UpdateModule

Apply simple property updates to items.

**Config Options**:
```python
{
    "operations": [
        {"type": "set_property", "key": "processing:level", "value": "L2A"},
        {"type": "delete_property", "key": "unwanted_field"}
    ]
}
```

**Usage**:
```python
from stac_manager.modules.update import UpdateModule

module = UpdateModule({
    "operations": [
        {"type": "set_property", "key": "custom:tag", "value": "processed"}
    ]
})

modified_item = await module.modify(item, context)
```

#### TransformModule

Complex transformations with enrichment and geometry operations.

**Config Options**:
```python
{
    "operations": [
        {"type": "enrich_from_sidecar", "source": "metadata.json"},
        {"type": "compute_bbox"},
        {"type": "normalize_links"}
    ]
}
```

**Usage**:
```python
from stac_manager.modules.transform import TransformModule

module = TransformModule({
    "operations": [
        {"type": "compute_bbox"},
        {"type": "enrich_from_sidecar", "source": "sidecars/{{id}}.json"}
    ]
})

transformed = await module.modify(item, context)
```

#### ValidateModule

Validate items against STAC JSON schemas.

**Config Options**:
```python
{
    "schema_version": "1.0.0",  # STAC version to validate against
    "strict": False  # True = raise on invalid, False = log to FailureCollector
}
```

**Usage**:
```python
from stac_manager.modules.validate import ValidateModule

module = ValidateModule({
    "schema_version": "1.0.0",
    "strict": False  # permissive mode
})

validated = await module.modify(item, context)
if validated is None:
    # Item failed validation, error logged to context
    failures = context.get_failures()
```

#### ExtensionModule

Add STAC extensions to items.

**Config Options**:
```python
{
    "extensions": [
        "https://stac-extensions.github.io/eo/v1.1.0/schema.json",
        "https://stac-extensions.github.io/projection/v1.1.0/schema.json"
    ]
}
```

**Usage**:
```python
from stac_manager.modules.extension import ExtensionModule

module = ExtensionModule({
    "extensions": ["https://stac-extensions.github.io/eo/v1.1.0/schema.json"]
})

extended = await module.modify(item, context)
assert "https://stac-extensions.github.io/eo/v1.1.0/schema.json" in extended["stac_extensions"]
```

### Bundler Modules

#### OutputModule

Write items to JSON files or Parquet.

**Config Options**:
```python
{
    "format": "json",  # or "parquet"
    "base_dir": "/path/to/output",
    "buffer_size": 100,  # flush threshold
    "base_url": "https://catalog.example.com/items",  # optional, updates self links
    "include_collection": True  # write collection.json
}
```

**JSON Output Usage**:
```python
from stac_manager.modules.output import OutputModule

module = OutputModule({
    "format": "json",
    "base_dir": "output/items",
    "base_url": "https://my-catalog.com/items"
})

# Bundle items
for item in items:
    await module.bundle(item, context)

# Finalize
result = await module.finalize(context)
print(f"Wrote {result['items_written']} items")
```

**Parquet Output Usage**:
```python
module = OutputModule({
    "format": "parquet",
    "base_dir": "output/",
    "buffer_size": 1000  # larger buffer for parquet
})

for item in items:
    await module.bundle(item, context)

await module.finalize(context)
# Creates output/items_<timestamp>.parquet
```

## Error Handling

All modules follow the three-tier error handling model:

1. **Tier 1 - Fail Fast**: Configuration errors raise `ConfigurationError` during `__init__`
2. **Tier 2 - Step Out**: Item-level errors logged to `FailureCollector` (when `strict=False`)
3. **Tier 3 - Graceful Degradation**: Optional features fail with warnings

Example of permissive error handling:

```python
# Configure module with strict=False
ingest = IngestModule({"mode": "file", "source": "items.json", "strict": False})

# Process items - failures logged, not raised
items = []
async for item in ingest.fetch(context):
    items.append(item)

# Check failures after processing
failures = context.get_failures()
for failure in failures:
    print(f"Item {failure['item_id']} failed: {failure['error']}")
```

## Context Integration

Modules interact with `WorkflowContext` for:

- **Logging**: `context.logger.info("message")`
- **Failure Collection**: `context.add_failure(item_id, error, stage)`
- **Data Sharing**: `context.data["key"] = value`

Context data can override module config for matrix strategies:

```python
# Module config has default source
ingest = IngestModule({"mode": "file", "source": "default.json"})

# Context data overrides for specific run
context.data["source"] = "override.json"

async for item in ingest.fetch(context):
    # Fetches from override.json
    pass
```

## Testing Modules

Example test pattern:

```python
import pytest
from stac_manager.modules.update import UpdateModule
from tests.fixtures.context import MockWorkflowContext
from tests.fixtures.stac_items import VALID_ITEM

@pytest.mark.asyncio
async def test_update_module():
    config = {
        "operations": [
            {"type": "set_property", "key": "test", "value": "value"}
        ]
    }
    
    module = UpdateModule(config)
    context = MockWorkflowContext.create()
    
    result = await module.modify(VALID_ITEM.copy(), context)
    
    assert result["properties"]["test"] == "value"
```

## Protocol Compliance

Verify module implements correct protocol:

```python
from stac_manager.protocols import Fetcher, Modifier, Bundler
from stac_manager.modules.ingest import IngestModule

def test_protocol_compliance():
    module = IngestModule({"mode": "file", "source": "test.json"})
    assert isinstance(module, Fetcher)
```
```

**Step 2: Review documentation for completeness**

Check that all 7 modules are documented:
- ✅ SeedModule (Fetcher)
- ✅ IngestModule (Fetcher)
- ✅ UpdateModule (Modifier)
- ✅ TransformModule (Modifier)
- ✅ ValidateModule (Modifier)
- ✅ ExtensionModule (Modifier)
- ✅ OutputModule (Bundler)

**Step 3: Add usage examples**

Documentation includes:
- Configuration schemas for each module
- Python usage examples
- Error handling patterns
- Context integration examples
- Testing patterns

**Step 4: Commit**

```bash
git add src/stac_manager/modules/README.md
git commit -m "docs(modules): add comprehensive module documentation"
```

---

### Task 56: Part 3 Verification & Coverage

**Files:**
- None (verification steps)

**Step 1: Run unit test suite with coverage**

Run: `pytest tests/unit/modules/ -v --cov=src/stac_manager/modules --cov-report=term-missing`

Expected output:
```
==================== test session starts ====================
collected 47 items

tests/unit/modules/test_extension.py .....           [ 10%]
tests/unit/modules/test_ingest.py .......            [ 25%]
tests/unit/modules/test_output.py ........           [ 42%]
tests/unit/modules/test_seed.py .....                [ 53%]
tests/unit/modules/test_transform.py ......          [ 66%]
tests/unit/modules/test_update.py .....              [ 76%]
tests/unit/modules/test_validate.py .......          [ 91%]

---------- coverage: platform linux, python 3.12.1 ----------
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
src/stac_manager/modules/__init__.py        7      0   100%
src/stac_manager/modules/config.py         45      0   100%
src/stac_manager/modules/extension.py      38      0   100%
src/stac_manager/modules/ingest.py         89      3    97%   145-147
src/stac_manager/modules/output.py         102     4    96%   178-181
src/stac_manager/modules/seed.py           28      0   100%
src/stac_manager/modules/transform.py      67      2    97%   92-94
src/stac_manager/modules/update.py         42      0   100%
src/stac_manager/modules/validate.py       51      1    98%   73
---------------------------------------------------------------------
TOTAL                                      469     10    98%

==================== 47 passed in 2.34s ====================
```

**Step 2: Run integration test suite**

Run: `pytest tests/integration/ -v`

Expected output:
```
==================== test session starts ====================
collected 3 items

tests/integration/test_pipeline_e2e.py::test_seed_update_output_pipeline PASSED
tests/integration/test_pipeline_e2e.py::test_complex_pipeline PASSED
tests/integration/test_pipeline_e2e.py::test_pipeline_failure_collection PASSED

==================== 3 passed in 1.89s ====================
```

**Step 3: Run type checking**

Run: `mypy src/stac_manager/modules --strict`

Expected output:
```
Success: no issues found in 8 source files
```

If type errors exist, fix them:
- Add missing type annotations
- Resolve `Any` types
- Fix protocol compliance issues

**Step 4: Generate Part 3 completion report**

Create summary document:

```markdown
# Phase 2 Part 3 Completion Report

## Modules Implemented

### Fetcher Modules
- ✅ **IngestModule**: File (JSON/Parquet) and API ingestion
  - File Mode: JSON FeatureCollection, Parquet via pyarrow
  - API Mode: pystac-client integration with bbox/datetime/query filters
  - Context data override support
  - Strict/permissive error handling

### Bundler Modules
- ✅ **OutputModule**: JSON and Parquet output
  - Buffering strategy with configurable flush threshold
  - Atomic writes using temp file + rename
  - Link management (self link updates)
  - Collection file generation
  - Parquet output via pyarrow

## Test Coverage

- **Unit Tests**: 47 tests, 98% coverage
- **Integration Tests**: 3 end-to-end pipeline tests
- **Total Lines**: 469 statements, 10 uncovered

## Protocol Compliance

All modules implement correct protocols:
- IngestModule → Fetcher
- OutputModule → Bundler

## Documentation

- ✅ Module README with config schemas
- ✅ Usage examples for all modules
- ✅ Error handling documentation
- ✅ Context integration examples

## Known Limitations

1. **API Pagination**: IngestModule does not handle paginated API responses beyond `max_items`
2. **Parquet Self Links**: Parquet output has all items point to same file (by design)
3. **Collection Links**: Collection file generation does not validate link structure

## Phase 2 Status

**All 7 Pipeline Modules Complete**:
- ✅ Part 1: Core Infrastructure (SeedModule, UpdateModule)
- ✅ Part 2: Modifier Modules (TransformModule, ValidateModule, ExtensionModule)
- ✅ Part 3: I/O Modules (IngestModule, OutputModule) + Integration Tests

**Ready for Phase 3**: Orchestration layer to compose module pipelines
```

**Step 5: Commit verification artifacts**

```bash
git add docs/reports/phase2-part3-completion.md
git commit -m "docs: add Phase 2 Part 3 completion report"
```

---

## Part 3 Summary

**Upon completion, Part 3 delivers:**

- **2 I/O-Heavy Modules**:
  - `IngestModule`: Multi-source fetcher (files + APIs)
  - `OutputModule`: Multi-format bundler (JSON + Parquet)

- **Full Protocol Implementations**:
  - Fetcher protocol: `fetch()` async generator
  - Bundler protocol: `bundle()` + `finalize()`

- **Comprehensive Testing**:
  - 16 unit tests for IngestModule/OutputModule
  - 3 end-to-end integration tests
  - 98% code coverage

- **Complete Documentation**:
  - Module README with all config options
  - Usage examples for Python users
  - Error handling patterns

**Phase 2 Complete**: All 7 pipeline modules (2 Fetchers, 4 Modifiers, 1 Bundler) fully implemented with TDD, achieving the project's core vision of modular, composable STAC data pipelines.
