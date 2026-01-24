# STAC Manager Phase 2 (Pipeline Modules) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

> **Context**: This is **Phase 2: Pipeline Modules** of the STAC Manager implementation.  
> See [Implementation Roadmap](./2026-01-22-stac-manager-roadmap.md) for complete context.

**Goal**: Implement the specialized pipeline components (Fetchers, Modifiers, Bundlers) that perform domain-specific STAC operations, building on the utilities foundation from Phase 1.

**Architecture**: Pipes and Filters pattern with protocol-based interfaces
- **Fetchers** (Sources): `IngestModule`, `SeedModule` - Async I/O for item retrieval
- **Modifiers** (Processors): `TransformModule`, `UpdateModule`, `ValidateModule`, `ExtensionModule` - Sync processing
- **Bundlers** (Sinks): `OutputModule` - Async I/O for output writing

**Tech Stack**: 
- Python 3.12+ (Protocols, structural pattern matching)
- PySTAC 1.10+, PySTAC-Client 0.7+, stac-validator, stac-geoparquet
- httpx (async HTTP), pandas (CSV reading), pyarrow (Parquet I/O)
- pytest, pytest-asyncio, pytest-cov

**Testing Philosophy**:
- TDD RED-GREEN-REFACTOR for every task
- No mocks on domain data (use real STAC items)
- Mock only infrastructure (HTTP, file I/O, WorkflowContext)
- ≥90% coverage including error paths

**Dependencies**: Phase 1 utilities (`stac_manager/utils/`) must be complete and tested.

---

## Table of Contents

### Phase 1: Core Infrastructure (Tasks 1-5)
- Task 1: Create module test fixtures
- Task 2: Implement WorkflowContext
- Task 3: Implement FailureCollector
- Task 4: Create protocol definitions
- Task 5: Create base module configuration models

### Phase 2: Seed Module (Tasks 6-10) - 5 tasks
Basic fetcher implementation for testing and scaffolding

### Phase 3: Update Module (Tasks 11-17) - 7 tasks
Field modification with dot-notation and patch support

### Phase 4: Validate Module (Tasks 18-21) - 4 tasks
STAC schema validation integration

### Phase 5: Extension Module (Tasks 22-27) - 6 tasks
Extension scaffolding and application

### Phase 6: Transform Module (Tasks 28-35) - 8 tasks
Sidecar data enrichment and field mapping

### Phase 7: Ingest Module (Tasks 36-44) - 9 tasks
API and file-based item fetching with parallelism

### Phase 8: Output Module (Tasks 45-51) - 7 tasks
JSON and Parquet output with atomic writes

### Phase 9: Integration & Verification (Tasks 52-56) - 5 tasks
End-to-end module interop and documentation

**Total Tasks**: 56 granular TDD tasks

---

## Phase 1: Core Infrastructure

### Task 1: Create Module Test Fixtures

**Files:**
- Create: `tests/fixtures/modules.py`
- Create: `tests/fixtures/context.py`

**Step 1: Create mock WorkflowContext fixture**

Create `tests/fixtures/context.py`:

```python
"""Mock WorkflowContext and infrastructure for module testing."""
from dataclasses import dataclass
from typing import Any
import logging


@dataclass
class MockFailureCollector:
    """Mock FailureCollector for testing."""
    failures: list[dict]
    
    def __init__(self):
        self.failures = []
    
    def add(self, item_id: str, error: str | Exception, step_id: str = 'unknown', error_context: dict | None = None) -> None:
        self.failures.append({
            'item_id': item_id,
            'error': str(error),
            'step_id': step_id,
            'context': error_context
        })


@dataclass
class MockCheckpointManager:
    """Mock CheckpointManager for testing."""
    
    def save(self, state: dict) -> None:
        pass
    
    def load(self) -> dict | None:
        return None


@dataclass
class MockWorkflowContext:
    """Mock WorkflowContext for module testing."""
    workflow_id: str
    config: dict
    logger: logging.Logger
    failure_collector: MockFailureCollector
    checkpoints: MockCheckpointManager
    data: dict[str, Any]
    
    @classmethod
    def create(cls, **kwargs):
        """Create mock context with defaults."""
        defaults = {
            'workflow_id': 'test-workflow-001',
            'config': {},
            'logger': logging.getLogger('test'),
            'failure_collector': MockFailureCollector(),
            'checkpoints': MockCheckpointManager(),
            'data': {}
        }
        defaults.update(kwargs)
        return cls(**defaults)
```

**Step 2: Create module test data fixtures**

Create `tests/fixtures/modules.py`:

```python
"""Test fixtures specific to pipeline modules."""

# Valid module configurations
SEED_CONFIG_BASIC = {
    "items": ["item-001", "item-002", "item-003"]
}

SEED_CONFIG_WITH_DEFAULTS = {
    "items": [
        "item-001",
        {"id": "item-002", "properties": {"platform": "Landsat-8"}}
    ],
    "defaults": {
        "collection": "test-collection",
        "properties": {
            "instrument": "OLI"
        }
    }
}

UPDATE_CONFIG_BASIC = {
    "updates": {
        "properties.license": "CC-BY-4.0"
    }
}

UPDATE_CONFIG_WITH_REMOVES = {
    "updates": {
        "properties.license": "CC-BY-4.0"
    },
    "removes": ["properties.deprecated_field"]
}
```

**Step 3: Commit**

```bash
git add tests/fixtures/context.py tests/fixtures/modules.py
git commit -m "test: add module test fixtures and mock context"
```

---

### Task 2: Implement WorkflowContext

**Files:**
- Create: `src/stac_manager/core/__init__.py`
- Create: `src/stac_manager/core/context.py`
- Create: `tests/unit/core/test_context.py`

**Step 1: Write failing test for WorkflowContext creation**

Create `tests/unit/core/test_context.py`:

```python
import pytest
import logging
from stac_manager.core.context import WorkflowContext
from tests.fixtures.context import MockFailureCollector, MockCheckpointManager


def test_workflow_context_creation():
    """WorkflowContext can be created with required fields."""
    ctx = WorkflowContext(
        workflow_id="test-001",
        config={"name": "test"},
        logger=logging.getLogger("test"),
        failure_collector=MockFailureCollector(),
        checkpoints=MockCheckpointManager(),
        data={"collection_id": "test-collection"}
    )
    
    assert ctx.workflow_id == "test-001"
    assert ctx.config["name"] == "test"
    assert ctx.data["collection_id"] == "test-collection"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/core/test_context.py::test_workflow_context_creation -v`  
Expected: FAIL with "ModuleNotFoundError: No module named 'stac_manager.core'"

**Step 3: Implement WorkflowContext**

Create `src/stac_manager/core/__init__.py`: (empty file)

Create `src/stac_manager/core/context.py`:

```python
"""Workflow execution context."""
from dataclasses import dataclass
from typing import Any
import logging


@dataclass
class WorkflowContext:
    """Shared state passed to all components during execution."""
    workflow_id: str
    config: dict
    logger: logging.Logger
    failure_collector: 'FailureCollector'
    checkpoints: 'CheckpointManager'
    data: dict[str, Any]
    
    def fork(self, data: dict[str, Any]) -> 'WorkflowContext':
        """
        Create a child context with isolated data.
        Used for Matrix Strategy to spawn parallel pipelines.
        """
        return WorkflowContext(
            workflow_id=self.workflow_id,
            config=self.config,
            logger=self.logger,
            failure_collector=self.failure_collector,
            checkpoints=self.checkpoints,
            data={**self.data, **data}
        )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/core/test_context.py::test_workflow_context_creation -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/stac_manager/core/ tests/unit/core/test_context.py
git commit -m "feat(core): add WorkflowContext dataclass"
```

---

### Task 3: Implement FailureCollector

**Files:**
- Create: `src/stac_manager/core/failures.py`
- Modify: `tests/unit/core/test_context.py`

**Step 1: Write failing test for FailureCollector**

Add to `tests/unit/core/test_context.py`:

```python
from stac_manager.core.failures import FailureCollector, FailureRecord


def test_failure_collector_add():
    """FailureCollector records failures."""
    collector = FailureCollector()
    
    collector.add(
        item_id="item-001",
        error="Validation failed",
        step_id="validate"
    )
    
    failures = collector.get_all()
    assert len(failures) == 1
    assert failures[0].item_id == "item-001"
    assert failures[0].error_type == "str"
    assert failures[0].message == "Validation failed"


def test_failure_collector_with_exception():
    """FailureCollector handles Exception objects."""
    collector = FailureCollector()
    
    try:
        raise ValueError("Test error")
    except ValueError as e:
        collector.add(
            item_id="item-002",
            error=e,
            step_id="transform"
        )
    
    failures = collector.get_all()
    assert len(failures) == 1
    assert failures[0].error_type == "ValueError"
    assert "Test error" in failures[0].message
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/core/test_context.py::test_failure_collector_add -v`  
Expected: FAIL with "ImportError: cannot import name 'FailureCollector'"

**Step 3: Implement FailureCollector**

Create `src/stac_manager/core/failures.py`:

```python
"""Failure collection and reporting."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TypedDict


class FailureContext(TypedDict, total=False):
    """Context for failure debugging."""
    source_file: str
    line_number: int
    field_name: str
    url: str
    http_status: int
    retry_attempt: int


@dataclass
class FailureRecord:
    """Single failure record."""
    step_id: str
    item_id: str
    error_type: str
    message: str
    timestamp: str
    context: FailureContext | None = None


class FailureCollector:
    """Collects non-critical failures for reporting."""
    
    def __init__(self):
        self._failures: list[FailureRecord] = []
    
    def add(
        self,
        item_id: str,
        error: str | Exception,
        step_id: str = 'unknown',
        error_context: FailureContext | None = None
    ) -> None:
        """Add a failure record."""
        if isinstance(error, Exception):
            error_type = type(error).__name__
            message = str(error)
        else:
            error_type = "str"
            message = error
        
        record = FailureRecord(
            step_id=step_id,
            item_id=item_id,
            error_type=error_type,
            message=message,
            timestamp=datetime.now(timezone.utc).isoformat(),
            context=error_context
        )
        self._failures.append(record)
    
    def get_all(self) -> list[FailureRecord]:
        """Get all collected failures."""
        return self._failures.copy()
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/core/test_context.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/core/failures.py tests/unit/core/test_context.py
git commit -m "feat(core): add FailureCollector for error aggregation"
```

---

### Task 4: Create Protocol Definitions

**Files:**
- Create: `src/stac_manager/protocols.py`
- Create: `tests/unit/test_protocols.py`

**Step 1: Write test for protocol compliance checking**

Create `tests/unit/test_protocols.py`:

```python
import pytest
from stac_manager.protocols import Fetcher, Modifier, Bundler
from stac_manager.core.context import WorkflowContext
from tests.fixtures.context import MockWorkflowContext


class MockFetcher:
    """Mock Fetcher implementation for testing."""
    
    def __init__(self, config: dict) -> None:
        self.config = config
    
    async def fetch(self, context: WorkflowContext):
        yield {"id": "test-001"}


def test_fetcher_protocol_compliance():
    """MockFetcher implements Fetcher protocol."""
    fetcher = MockFetcher({"test": True})
    
    # Protocol check (runtime checkable)
    assert isinstance(fetcher, Fetcher)
    assert hasattr(fetcher, 'fetch')
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_protocols.py::test_fetcher_protocol_compliance -v`  
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Implement protocols**

Create `src/stac_manager/protocols.py`:

```python
"""Protocol definitions for pipeline components."""
from typing import Protocol, AsyncIterator, runtime_checkable


@runtime_checkable
class Fetcher(Protocol):
    """Retrieves items from external or local sources."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with step-specific configuration."""
        ...
    
    async def fetch(self, context: 'WorkflowContext') -> AsyncIterator[dict]:
        """
        Originate a stream of STAC Items or Collections.
        
        Yields:
            STAC item dicts
        """
        ...


@runtime_checkable
class Modifier(Protocol):
    """Transforms or validates a single STAC Item/Collection."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with step-specific configuration."""
        ...
    
    def modify(self, item: dict, context: 'WorkflowContext') -> dict | None:
        """
        Process a single item.
        
        Args:
            item: STAC item dict
            context: Workflow context
        
        Returns:
            Modified dict or None to filter out item
        """
        ...


@runtime_checkable
class Bundler(Protocol):
    """Finalizes and writes items to storage."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with step-specific configuration."""
        ...
    
    async def bundle(self, item: dict, context: 'WorkflowContext') -> None:
        """
        Add an item to the current bundle/buffer.
        
        Must be non-blocking async.
        """
        ...
    
    async def finalize(self, context: 'WorkflowContext') -> dict:
        """
        Commit any remaining buffers and return execution manifest.
        
        Returns:
            OutputResult-compatible dict
        """
        ...
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_protocols.py::test_fetcher_protocol_compliance -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/stac_manager/protocols.py tests/unit/test_protocols.py
git commit -m "feat: add Fetcher/Modifier/Bundler protocol definitions"
```

---

### Task 5: Create Base Module Configuration Models

**Files:**
- Create: `src/stac_manager/modules/__init__.py`
- Create: `src/stac_manager/modules/config.py`
- Create: `tests/unit/modules/test_config.py`

**Step 1: Write failing test for Pydantic config models**

Create `tests/unit/modules/test_config.py`:

```python
import pytest
from pydantic import ValidationError
from stac_manager.modules.config import SeedConfig, UpdateConfig, ValidateConfig


def test_seed_config_validation():
    """SeedConfig validates required fields."""
    config = SeedConfig(items=["item-001", "item-002"])
    assert config.items == ["item-001", "item-002"]
    assert config.source_file is None


def test_seed_config_with_defaults():
    """SeedConfig accepts defaults."""
    config = SeedConfig(
        items=["item-001"],
        defaults={"collection": "test"}
    )
    assert config.defaults["collection"] == "test"


def test_update_config_validation():
    """UpdateConfig validates updates dict."""
    config = UpdateConfig(
        updates={"properties.license": "CC-BY-4.0"}
    )
    assert config.updates["properties.license"] == "CC-BY-4.0"
    assert config.auto_update_timestamp is True  # default


def test_validate_config_defaults():
    """ValidateConfig uses defaults."""
    config = ValidateConfig()
    assert config.strict is False
    assert config.extension_schemas == []
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_config.py::test_seed_config_validation -v`  
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Implement config models**

Create `src/stac_manager/modules/__init__.py`: (empty file)

Create `src/stac_manager/modules/config.py`:

```python
"""Pydantic configuration models for pipeline modules."""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any, List, Union, Literal


class SeedConfig(BaseModel):
    """Configuration for SeedModule."""
    items: Optional[List[Union[str, Dict[str, Any]]]] = None
    source_file: Optional[str] = None
    defaults: Optional[Dict[str, Any]] = None


class UpdateConfig(BaseModel):
    """Configuration for UpdateModule."""
    updates: Optional[Dict[str, Any]] = None
    removes: Optional[List[str]] = None
    patch_file: Optional[str] = None
    mode: Literal['merge', 'replace'] = 'merge'
    create_missing_paths: bool = True
    auto_update_timestamp: bool = True


class ValidateConfig(BaseModel):
    """Configuration for ValidateModule."""
    strict: bool = False
    extension_schemas: List[HttpUrl] = Field(default_factory=list)


class ExtensionConfig(BaseModel):
    """Configuration for ExtensionModule."""
    schema_uri: str
    defaults: Optional[Dict[str, Any]] = None
    validate: bool = False


class TransformConfig(BaseModel):
    """Configuration for TransformModule."""
    input_file: Optional[str] = None
    strategy: Literal['merge', 'update'] = 'merge'
    sidecar_id_path: str = "id"
    data_path: Optional[str] = None
    schema_file: Optional[str] = None
    schema_mapping: Optional[Dict[str, Any]] = Field(alias='schema', default=None)


class IngestFilters(BaseModel):
    """Common filters for STAC API searches."""
    bbox: Optional[List[float]] = None
    datetime: Optional[str] = None
    query: Optional[Dict[str, Any]] = None
    ids: Optional[List[str]] = None


class IngestConfig(BaseModel):
    """Configuration for IngestModule."""
    catalog_url: Optional[str] = None
    collection_id: Optional[str] = None
    source_file: Optional[str] = None
    concurrency: int = Field(default=10, ge=1)
    filters: Optional[IngestFilters] = None


class OutputConfig(BaseModel):
    """Configuration for OutputModule."""
    base_dir: str
    format: Literal['json', 'parquet'] = 'json'
    base_url: Optional[str] = Field(alias='BASE_URL', default=None)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_config.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/ tests/unit/modules/test_config.py
git commit -m "feat(modules): add Pydantic configuration models"
```

---

## Phase 2: Seed Module

### Task 6: Seed Module - Basic Item Yielding

**Files:**
- Create: `src/stac_manager/modules/seed.py`
- Create: `tests/unit/modules/test_seed.py`

**Step 1: Write failing test for basic seed module**

Create `tests/unit/modules/test_seed.py`:

```python
import pytest
from stac_manager.modules.seed import SeedModule
from tests.fixtures.context import MockWorkflowContext
from tests.fixtures.modules import SEED_CONFIG_BASIC


@pytest.mark.asyncio
async def test_seed_module_yields_string_items():
    """SeedModule yields items from string list."""
    module = SeedModule(SEED_CONFIG_BASIC)
    context = MockWorkflowContext.create()
    
    items = []
    async for item in module.fetch(context):
        items.append(item)
    
    assert len(items) == 3
    assert items[0]["id"] == "item-001"
    assert items[1]["id"] == "item-002"
    assert items[2]["id"] == "item-003"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_seed.py::test_seed_module_yields_string_items -v`  
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `src/stac_manager/modules/seed.py`:

```python
"""Seed Module - Generator source for skeleton items."""
from typing import AsyncIterator
from stac_manager.modules.config import SeedConfig
from stac_manager.core.context import WorkflowContext


class SeedModule:
    """Yields skeleton STAC Items from configured list."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with configuration."""
        self.config = SeedConfig(**config)
    
    async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
        """
        Yields items from config or source file.
        
        Args:
            context: Workflow context
        
        Yields:
            STAC item dicts
        """
        items_list = self.config.items or []
        
        for item_entry in items_list:
            item_dict = {}
            
            # Normalize to dict
            if isinstance(item_entry, str):
                item_dict = {"id": item_entry}
            elif isinstance(item_entry, dict):
                item_dict = item_entry.copy()
            else:
                raise ValueError(f"Invalid item format: {type(item_entry)}")
            
            yield item_dict
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/modules/test_seed.py::test_seed_module_yields_string_items -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/seed.py tests/unit/modules/test_seed.py
git commit -m "feat(modules): add basic SeedModule implementation"
```

---

### Task 7: Seed Module - Defaults Application

**Files:**
- Modify: `tests/unit/modules/test_seed.py`
- Modify: `src/stac_manager/modules/seed.py`

**Step 1: Write failing test for defaults**

Add to `tests/unit/modules/test_seed.py`:

```python
from tests.fixtures.modules import SEED_CONFIG_WITH_DEFAULTS


@pytest.mark.asyncio
async def test_seed_module_applies_defaults():
    """SeedModule applies default values to items."""
    module = SeedModule(SEED_CONFIG_WITH_DEFAULTS)
    context = MockWorkflowContext.create()
    
    items = []
    async for item in module.fetch(context):
        items.append(item)
    
    # First item (string) gets full defaults
    assert items[0]["id"] == "item-001"
    assert items[0]["collection"] == "test-collection"
    assert items[0]["properties"]["instrument"] == "OLI"
    
    # Second item (dict) merges with defaults
    assert items[1]["id"] == "item-002"
    assert items[1]["collection"] == "test-collection"
    assert items[1]["properties"]["platform"] == "Landsat-8"  # Item-specific
    assert items[1]["properties"]["instrument"] == "OLI"  # From defaults
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_seed.py::test_seed_module_applies_defaults -v`  
Expected: FAIL with "KeyError: 'collection'"

**Step 3: Implement defaults application**

Update `src/stac_manager/modules/seed.py`:

```python
"""Seed Module - Generator source for skeleton items."""
from typing import AsyncIterator
from stac_manager.modules.config import SeedConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.utils.field_ops import deep_merge


class SeedModule:
    """Yields skeleton STAC Items from configured list."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with configuration."""
        self.config = SeedConfig(**config)
    
    async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
        """
        Yields items from config or source file.
        
        Args:
            context: Workflow context
        
        Yields:
            STAC item dicts
        """
        items_list = self.config.items or []
        
        for item_entry in items_list:
            item_dict = {}
            
            # Normalize to dict
            if isinstance(item_entry, str):
                item_dict = {"id": item_entry}
            elif isinstance(item_entry, dict):
                item_dict = item_entry.copy()
            else:
                raise ValueError(f"Invalid item format: {type(item_entry)}")
            
            # Apply defaults (defaults as base, item overrides)
            if self.config.defaults:
                final_item = self.config.defaults.copy()
                final_item = deep_merge(final_item, item_dict, strategy='overwrite')
                item_dict = final_item
            
            yield item_dict
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_seed.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/seed.py tests/unit/modules/test_seed.py
git commit -m "feat(modules): add defaults application to SeedModule"
```

---

### Task 8: Seed Module - Context Enrichment

**Files:**
- Modify: `tests/unit/modules/test_seed.py`
- Modify: `src/stac_manager/modules/seed.py`

**Step 1: Write failing test for context enrichment**

Add to `tests/unit/modules/test_seed.py`:

```python
@pytest.mark.asyncio
async def test_seed_module_context_enrichment():
    """SeedModule enriches items from context.data."""
    module = SeedModule({"items": ["item-001"]})
    context = MockWorkflowContext.create(
        data={"collection_id": "landsat-c2"}
    )
    
    items = []
    async for item in module.fetch(context):
        items.append(item)
    
    assert items[0]["collection"] == "landsat-c2"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_seed.py::test_seed_module_context_enrichment -v`  
Expected: FAIL with "KeyError: 'collection'"

**Step 3: Implement context enrichment**

Update `src/stac_manager/modules/seed.py` fetch method:

```python
    async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
        """
        Yields items from config or source file.
        
        Args:
            context: Workflow context
        
        Yields:
            STAC item dicts
        """
        items_list = self.config.items or []
        
        for item_entry in items_list:
            item_dict = {}
            
            # Normalize to dict
            if isinstance(item_entry, str):
                item_dict = {"id": item_entry}
            elif isinstance(item_entry, dict):
                item_dict = item_entry.copy()
            else:
                raise ValueError(f"Invalid item format: {type(item_entry)}")
            
            # Apply defaults (defaults as base, item overrides)
            if self.config.defaults:
                final_item = self.config.defaults.copy()
                final_item = deep_merge(final_item, item_dict, strategy='overwrite')
                item_dict = final_item
            
            # Context enrichment
            if "collection" not in item_dict and "collection_id" in context.data:
                item_dict["collection"] = context.data["collection_id"]
            
            yield item_dict
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_seed.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/seed.py tests/unit/modules/test_seed.py
git commit -m "feat(modules): add context enrichment to SeedModule"
```

---

### Task 9: Seed Module - File Loading Support

**Files:**
- Modify: `tests/unit/modules/test_seed.py`
- Modify: `src/stac_manager/modules/seed.py`

**Step 1: Write failing test for file loading**

Add to `tests/unit/modules/test_seed.py`:

```python
import tempfile
import json


@pytest.mark.asyncio
async def test_seed_module_loads_from_file():
    """SeedModule loads items from source_file."""
    # Create temp JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(["file-item-001", "file-item-002"], f)
        temp_path = f.name
    
    try:
        module = SeedModule({"source_file": temp_path})
        context = MockWorkflowContext.create()
        
        items = []
        async for item in module.fetch(context):
            items.append(item)
        
        assert len(items) == 2
        assert items[0]["id"] == "file-item-001"
        assert items[1]["id"] == "file-item-002"
    finally:
        import os
        os.unlink(temp_path)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_seed.py::test_seed_module_loads_from_file -v`  
Expected: FAIL (no file loading implemented)

**Step 3: Implement file loading**

Update `src/stac_manager/modules/seed.py`:

```python
"""Seed Module - Generator source for skeleton items."""
import json
from typing import AsyncIterator
from pathlib import Path
from stac_manager.modules.config import SeedConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.utils.field_ops import deep_merge
from stac_manager.exceptions import ConfigurationError


class SeedModule:
    """Yields skeleton STAC Items from configured list."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with configuration."""
        self.config = SeedConfig(**config)
    
    async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
        """
        Yields items from config or source file.
        
        Args:
            context: Workflow context
        
        Yields:
            STAC item dicts
        """
        items_list = []
        
        # Load from file if specified
        if self.config.source_file:
            file_path = Path(self.config.source_file)
            if not file_path.exists():
                raise ConfigurationError(f"source_file not found: {self.config.source_file}")
            
            with open(file_path, 'r') as f:
                file_items = json.load(f)
            
            if not isinstance(file_items, list):
                raise ConfigurationError("source_file must contain a JSON array")
            
            items_list.extend(file_items)
        
        # Add inline items
        if self.config.items:
            items_list.extend(self.config.items)
        
        if not items_list:
            context.logger.warning("SeedModule: No items to yield.")
            return
        
        for item_entry in items_list:
            item_dict = {}
            
            # Normalize to dict
            if isinstance(item_entry, str):
                item_dict = {"id": item_entry}
            elif isinstance(item_entry, dict):
                item_dict = item_entry.copy()
            else:
                raise ValueError(f"Invalid item format: {type(item_entry)}")
            
            # Apply defaults (defaults as base, item overrides)
            if self.config.defaults:
                final_item = self.config.defaults.copy()
                final_item = deep_merge(final_item, item_dict, strategy='overwrite')
                item_dict = final_item
            
            # Context enrichment
            if "collection" not in item_dict and "collection_id" in context.data:
                item_dict["collection"] = context.data["collection_id"]
            
            yield item_dict
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_seed.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/seed.py tests/unit/modules/test_seed.py
git commit -m "feat(modules): add file loading support to SeedModule"
```

---

### Task 10: Seed Module - Protocol Compliance

**Files:**
- Modify: `tests/unit/modules/test_seed.py`

**Step 1: Write test for protocol compliance**

Add to `tests/unit/modules/test_seed.py`:

```python
from stac_manager.protocols import Fetcher


def test_seed_module_implements_fetcher_protocol():
    """SeedModule implements Fetcher protocol."""
    module = SeedModule({"items": ["test"]})
    assert isinstance(module, Fetcher)
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/unit/modules/test_seed.py::test_seed_module_implements_fetcher_protocol -v`  
Expected: PASS (already complies)

**Step 3: Run full test suite**

Run: `pytest tests/unit/modules/test_seed.py -v`  
Expected: All PASS

**Step 4: Commit**

```bash
git add tests/unit/modules/test_seed.py
git commit -m "test(modules): verify SeedModule protocol compliance"
```

---

## Phase 3: Update Module

### Task 11: Update Module - Basic Field Updates

**Files:**
- Create: `src/stac_manager/modules/update.py`
- Create: `tests/unit/modules/test_update.py`

**Step 1: Write failing test for basic updates**

Create `tests/unit/modules/test_update.py`:

```python
import pytest
from stac_manager.modules.update import UpdateModule
from tests.fixtures.context import MockWorkflowContext
from tests.fixtures.stac_items import VALID_ITEM


def test_update_module_sets_field():
    """UpdateModule sets top-level field."""
    module = UpdateModule({
        "updates": {"properties.license": "CC-BY-4.0"}
    })
    context = MockWorkflowContext.create()
    
    item = VALID_ITEM.copy()
    result = module.modify(item, context)
    
    assert result["properties"]["license"] == "CC-BY-4.0"
    assert result["properties"]["datetime"] == "2024-01-01T00:00:00Z"  # Unchanged
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_update.py::test_update_module_sets_field -v`  
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `src/stac_manager/modules/update.py`:

```python
"""Update Module - Modifies existing STAC fields."""
from stac_manager.modules.config import UpdateConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.utils.field_ops import set_nested_field


class UpdateModule:
    """Modifies existing STAC Items."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with configuration."""
        self.config = UpdateConfig(**config)
    
    def modify(self, item: dict, context: WorkflowContext) -> dict:
        """
        Applies updates to the item.
        
        Args:
            item: STAC item dict
            context: Workflow context
        
        Returns:
            Modified item
        """
        # Apply global updates
        if self.config.updates:
            for path, value in self.config.updates.items():
                set_nested_field(item, path, value)
        
        return item
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/modules/test_update.py::test_update_module_sets_field -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/update.py tests/unit/modules/test_update.py
git commit -m "feat(modules): add basic UpdateModule implementation"
```

---

### Task 12: Update Module - Field Removal

**Files:**
- Modify: `tests/unit/modules/test_update.py`
- Modify: `src/stac_manager/modules/update.py`

**Step 1: Write failing test for removes**

Add to `tests/unit/modules/test_update.py`:

```python
from tests.fixtures.stac_items import NESTED_ITEM


def test_update_module_removes_field():
    """UpdateModule removes specified field."""
    item = NESTED_ITEM.copy()
    item["properties"]["deprecated"] = "old-value"
    
    module = UpdateModule({
        "removes": ["properties.deprecated"]
    })
    context = MockWorkflowContext.create()
    
    result = module.modify(item, context)
    
    assert "deprecated" not in result["properties"]
    assert "eo:cloud_cover" in result["properties"]  # Other fields intact
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_update.py::test_update_module_removes_field -v`  
Expected: FAIL with "AssertionError: 'deprecated' in properties"

**Step 3: Implement field removal**

Add helper function and update modify method in `src/stac_manager/modules/update.py`:

```python
"""Update Module - Modifies existing STAC fields."""
from stac_manager.modules.config import UpdateConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.utils.field_ops import set_nested_field, get_nested_field


def remove_nested_field(item: dict, path: str) -> None:
    """
    Remove nested field using dot notation.
    Idempotent - no error if path doesn't exist.
    
    Args:
        item: STAC item dict (modified in-place)
        path: Dot-separated path
    """
    keys = path.split('.')
    current = item
    
    # Navigate to parent
    for key in keys[:-1]:
        if not isinstance(current, dict) or key not in current:
            return  # Path doesn't exist, nothing to remove
        current = current[key]
    
    # Remove final key
    if isinstance(current, dict) and keys[-1] in current:
        del current[keys[-1]]


class UpdateModule:
    """Modifies existing STAC Items."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with configuration."""
        self.config = UpdateConfig(**config)
    
    def modify(self, item: dict, context: WorkflowContext) -> dict:
        """
        Applies updates to the item.
        
        Args:
            item: STAC item dict
            context: Workflow context
        
        Returns:
            Modified item
        """
        # 1. Apply global removals
        if self.config.removes:
            for path in self.config.removes:
                remove_nested_field(item, path)
        
        # 2. Apply global updates
        if self.config.updates:
            for path, value in self.config.updates.items():
                set_nested_field(item, path, value)
        
        return item
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_update.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/update.py tests/unit/modules/test_update.py
git commit -m "feat(modules): add field removal to UpdateModule"
```

---

### Task 13: Update Module - Patch File Support

**Files:**
- Modify: `tests/unit/modules/test_update.py`
- Modify: `src/stac_manager/modules/update.py`

**Step 1: Write failing test for patch file**

Add to `tests/unit/modules/test_update.py`:

```python
import tempfile
import json


def test_update_module_applies_patch_file():
    """UpdateModule applies item-specific patches from file."""
    # Create patch file
    patches = {
        "test-item-001": {
            "properties.eo:cloud_cover": 25.5
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(patches, f)
        temp_path = f.name
    
    try:
        module = UpdateModule({"patch_file": temp_path})
        context = MockWorkflowContext.create()
        
        item = VALID_ITEM.copy()
        result = module.modify(item, context)
        
        assert result["properties"]["eo:cloud_cover"] == 25.5
    finally:
        import os
        os.unlink(temp_path)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_update.py::test_update_module_applies_patch_file -v`  
Expected: FAIL with "KeyError: 'eo:cloud_cover'"

**Step 3: Implement patch file loading**

Update `src/stac_manager/modules/update.py`:

```python
"""Update Module - Modifies existing STAC fields."""
import json
from pathlib import Path
from stac_manager.modules.config import UpdateConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.utils.field_ops import set_nested_field
from stac_manager.exceptions import ConfigurationError


def remove_nested_field(item: dict, path: str) -> None:
    """Remove nested field using dot notation. Idempotent."""
    keys = path.split('.')
    current = item
    
    for key in keys[:-1]:
        if not isinstance(current, dict) or key not in current:
            return
        current = current[key]
    
    if isinstance(current, dict) and keys[-1] in current:
        del current[keys[-1]]


class UpdateModule:
    """Modifies existing STAC Items."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with configuration."""
        self.config = UpdateConfig(**config)
        self.patches: dict[str, dict] = {}
        
        # Load patch file
        if self.config.patch_file:
            patch_path = Path(self.config.patch_file)
            if not patch_path.exists():
                raise ConfigurationError(f"patch_file not found: {self.config.patch_file}")
            
            with open(patch_path, 'r') as f:
                self.patches = json.load(f)
    
    def modify(self, item: dict, context: WorkflowContext) -> dict:
        """
        Applies updates to the item.
        
        Args:
            item: STAC item dict
            context: Workflow context
        
        Returns:
            Modified item
        """
        # 1. Apply global removals
        if self.config.removes:
            for path in self.config.removes:
                remove_nested_field(item, path)
        
        # 2. Apply global updates
        if self.config.updates:
            for path, value in self.config.updates.items():
                set_nested_field(item, path, value)
        
        # 3. Apply item-specific patches
        item_id = item.get("id")
        if item_id and item_id in self.patches:
            for path, value in self.patches[item_id].items():
                set_nested_field(item, path, value)
        
        return item
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_update.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/update.py tests/unit/modules/test_update.py
git commit -m "feat(modules): add patch file support to UpdateModule"
```

---

### Task 14: Update Module - Auto Timestamp

**Files:**
- Modify: `tests/unit/modules/test_update.py`
- Modify: `src/stac_manager/modules/update.py`

**Step 1: Write failing test for auto timestamp**

Add to `tests/unit/modules/test_update.py`:

```python
from datetime import datetime, timezone


def test_update_module_auto_timestamp():
    """UpdateModule auto-updates timestamp."""
    module = UpdateModule({
        "updates": {"properties.license": "CC-BY-4.0"},
        "auto_update_timestamp": True
    })
    context = MockWorkflowContext.create()
    
    item = VALID_ITEM.copy()
    before = datetime.now(timezone.utc).isoformat()
    
    result = module.modify(item, context)
    
    assert "updated" in result["properties"]
    # Verify it's a valid ISO timestamp
    updated_time = datetime.fromisoformat(result["properties"]["updated"].replace("Z", "+00:00"))
    assert updated_time >= datetime.fromisoformat(before.replace("Z", "+00:00"))


def test_update_module_no_auto_timestamp():
    """UpdateModule respects auto_update_timestamp=False."""
    module = UpdateModule({
        "updates": {"properties.license": "CC-BY-4.0"},
        "auto_update_timestamp": False
    })
    context = MockWorkflowContext.create()
    
    item = VALID_ITEM.copy()
    result = module.modify(item, context)
    
    assert "updated" not in result["properties"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_update.py::test_update_module_auto_timestamp -v`  
Expected: FAIL with "KeyError: 'updated'"

**Step 3: Implement auto timestamp**

Update modify method in `src/stac_manager/modules/update.py`:

```python
"""Update Module - Modifies existing STAC fields."""
import json
from pathlib import Path
from datetime import datetime, timezone
from stac_manager.modules.config import UpdateConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.utils.field_ops import set_nested_field
from stac_manager.exceptions import ConfigurationError


def remove_nested_field(item: dict, path: str) -> None:
    """Remove nested field using dot notation. Idempotent."""
    keys = path.split('.')
    current = item
    
    for key in keys[:-1]:
        if not isinstance(current, dict) or key not in current:
            return
        current = current[key]
    
    if isinstance(current, dict) and keys[-1] in current:
        del current[keys[-1]]


class UpdateModule:
    """Modifies existing STAC Items."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with configuration."""
        self.config = UpdateConfig(**config)
        self.patches: dict[str, dict] = {}
        
        # Load patch file
        if self.config.patch_file:
            patch_path = Path(self.config.patch_file)
            if not patch_path.exists():
                raise ConfigurationError(f"patch_file not found: {self.config.patch_file}")
            
            with open(patch_path, 'r') as f:
                self.patches = json.load(f)
    
    def modify(self, item: dict, context: WorkflowContext) -> dict:
        """
        Applies updates to the item.
        
        Args:
            item: STAC item dict
            context: Workflow context
        
        Returns:
            Modified item
        """
        # 1. Apply global removals
        if self.config.removes:
            for path in self.config.removes:
                remove_nested_field(item, path)
        
        # 2. Apply global updates
        if self.config.updates:
            for path, value in self.config.updates.items():
                set_nested_field(item, path, value)
        
        # 3. Apply item-specific patches
        item_id = item.get("id")
        if item_id and item_id in self.patches:
            for path, value in self.patches[item_id].items():
                set_nested_field(item, path, value)
        
        # 4. Auto-update timestamp
        if self.config.auto_update_timestamp:
            timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            set_nested_field(item, "properties.updated", timestamp)
        
        return item
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_update.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/update.py tests/unit/modules/test_update.py
git commit -m "feat(modules): add auto timestamp to UpdateModule"
```

---

---

### Task 15: Update Module - Path Creation Behavior

**Files:**
- Modify: `tests/unit/modules/test_update.py`
- Modify: `src/stac_manager/modules/update.py`

**Step 1: Write failing test for create_missing_paths**

Add to `tests/unit/modules/test_update.py`:

```python
from stac_manager.exceptions import DataProcessingError


def test_update_module_creates_missing_paths():
    """UpdateModule creates missing nested structures."""
    module = UpdateModule({
        "updates": {"properties.custom_ext.field": "value"},
        "create_missing_paths": True
    })
    context = MockWorkflowContext.create()
    
    item = VALID_ITEM.copy()
    result = module.modify(item, context)
    
    assert result["properties"]["custom_ext"]["field"] == "value"


def test_update_module_no_create_missing_paths():
    """UpdateModule respects create_missing_paths=False."""
    module = UpdateModule({
        "updates": {"properties.custom_ext.field": "value"},
        "create_missing_paths": False
    })
    context = MockWorkflowContext.create()
    
    item = VALID_ITEM.copy()
    
    with pytest.raises(DataProcessingError):
        module.modify(item, context)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_update.py::test_update_module_creates_missing_paths -v`  
Expected: FAIL (create_missing_paths not implemented)

**Step 3: Enhance set_nested_field to support create_missing_paths**

Update UpdateModule class in `src/stac_manager/modules/update.py`:

```python
"""Update Module - Modifies existing STAC fields."""
import json
from pathlib import Path
from datetime import datetime, timezone
from stac_manager.modules.config import UpdateConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import ConfigurationError, DataProcessingError


def remove_nested_field(item: dict, path: str) -> None:
    """Remove nested field using dot notation. Idempotent."""
    keys = path.split('.')
    current = item
    
    for key in keys[:-1]:
        if not isinstance(current, dict) or key not in current:
            return
        current = current[key]
    
    if isinstance(current, dict) and keys[-1] in current:
        del current[keys[-1]]


def set_field_with_path_creation(item: dict, path: str, value: any, create_paths: bool) -> None:
    """
    Set nested field with optional path creation.
    
    Args:
        item: STAC item dict (modified in-place)
        path: Dot-separated path
        value: Value to set
        create_paths: If True, create missing intermediate dicts
    
    Raises:
        DataProcessingError: If path doesn't exist and create_paths=False
    """
    keys = path.split('.')
    current = item
    
    for i, key in enumerate(keys[:-1]):
        if key not in current:
            if not create_paths:
                raise DataProcessingError(f"Path does not exist: {'.'.join(keys[:i+1])}")
            current[key] = {}
        
        if not isinstance(current[key], dict):
            raise DataProcessingError(f"Cannot traverse non-dict at: {'.'.join(keys[:i+1])}")
        
        current = current[key]
    
    current[keys[-1]] = value


class UpdateModule:
    """Modifies existing STAC Items."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with configuration."""
        self.config = UpdateConfig(**config)
        self.patches: dict[str, dict] = {}
        
        # Load patch file
        if self.config.patch_file:
            patch_path = Path(self.config.patch_file)
            if not patch_path.exists():
                raise ConfigurationError(f"patch_file not found: {self.config.patch_file}")
            
            with open(patch_path, 'r') as f:
                self.patches = json.load(f)
    
    def modify(self, item: dict, context: WorkflowContext) -> dict:
        """
        Applies updates to the item.
        
        Args:
            item: STAC item dict
            context: Workflow context
        
        Returns:
            Modified item
        """
        # 1. Apply global removals
        if self.config.removes:
            for path in self.config.removes:
                remove_nested_field(item, path)
        
        # 2. Apply global updates
        if self.config.updates:
            for path, value in self.config.updates.items():
                set_field_with_path_creation(
                    item, path, value, 
                    create_paths=self.config.create_missing_paths
                )
        
        # 3. Apply item-specific patches
        item_id = item.get("id")
        if item_id and item_id in self.patches:
            for path, value in self.patches[item_id].items():
                set_field_with_path_creation(
                    item, path, value,
                    create_paths=self.config.create_missing_paths
                )
        
        # 4. Auto-update timestamp
        if self.config.auto_update_timestamp:
            timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            set_field_with_path_creation(
                item, "properties.updated", timestamp,
                create_paths=True  # Always create for timestamp
            )
        
        return item
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_update.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/update.py tests/unit/modules/test_update.py
git commit -m "feat(modules): add create_missing_paths support to UpdateModule"
```

---

### Task 16: Update Module - Error Handling

**Files:**
- Modify: `tests/unit/modules/test_update.py`

**Step 1: Write test for path collision error**

Add to `tests/unit/modules/test_update.py`:

```python
def test_update_module_path_collision_error():
    """UpdateModule raises error on path collision."""
    module = UpdateModule({
        "updates": {"properties.datetime.invalid": "value"}
    })
    context = MockWorkflowContext.create()
    
    item = VALID_ITEM.copy()
    # datetime is a string, can't traverse it
    
    with pytest.raises(DataProcessingError) as exc_info:
        module.modify(item, context)
    
    assert "Cannot traverse non-dict" in str(exc_info.value)
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/unit/modules/test_update.py::test_update_module_path_collision_error -v`  
Expected: PASS (already implemented in Task 15)

**Step 3: Run full UpdateModule test suite**

Run: `pytest tests/unit/modules/test_update.py -v`  
Expected: All PASS

**Step 4: Commit**

```bash
git add tests/unit/modules/test_update.py
git commit -m "test(modules): verify UpdateModule error handling"
```

---

### Task 17: Update Module - Protocol Compliance & Integration

**Files:**
- Modify: `tests/unit/modules/test_update.py`
- Modify: `src/stac_manager/modules/__init__.py`

**Step 1: Write test for protocol compliance**

Add to `tests/unit/modules/test_update.py`:

```python
from stac_manager.protocols import Modifier


def test_update_module_implements_modifier_protocol():
    """UpdateModule implements Modifier protocol."""
    module = UpdateModule({"updates": {"properties.test": "value"}})
    assert isinstance(module, Modifier)
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/unit/modules/test_update.py::test_update_module_implements_modifier_protocol -v`  
Expected: PASS (already complies)

**Step 3: Add module exports to __init__.py**

Update `src/stac_manager/modules/__init__.py`:

```python
"""Pipeline module implementations."""
from stac_manager.modules.seed import SeedModule
from stac_manager.modules.update import UpdateModule

__all__ = [
    'SeedModule',
    'UpdateModule',
]
```

**Step 4: Run full module test suite**

Run: `pytest tests/unit/modules/ -v`  
Expected: All PASS (SeedModule + UpdateModule)

**Step 5: Commit**

```bash
git add src/stac_manager/modules/__init__.py tests/unit/modules/test_update.py
git commit -m "feat(modules): complete UpdateModule with protocol compliance"
```

---

## Part 1 Summary & Verification

### Completed Tasks: 1-17

**Phase 1: Core Infrastructure** ✅
- Task 1: Module test fixtures (MockWorkflowContext, MockFailureCollector)
- Task 2: WorkflowContext dataclass
- Task 3: FailureCollector implementation
- Task 4: Protocol definitions (Fetcher, Modifier, Bundler)
- Task 5: Pydantic configuration models

**Phase 2: Seed Module** ✅
- Task 6: Basic item yielding from string list
- Task 7: Defaults application with deep_merge
- Task 8: Context enrichment from workflow data
- Task 9: File loading support (JSON arrays)
- Task 10: Protocol compliance verification

**Phase 3: Update Module** ✅
- Task 11: Basic field updates with dot notation
- Task 12: Field removal (idempotent)
- Task 13: Patch file support (item-specific updates)
- Task 14: Auto timestamp generation
- Task 15: Path creation behavior control
- Task 16: Error handling (path collisions)
- Task 17: Protocol compliance & module exports

### Files Created

**Production Code:**
- `src/stac_manager/core/__init__.py`
- `src/stac_manager/core/context.py`
- `src/stac_manager/core/failures.py`
- `src/stac_manager/protocols.py`
- `src/stac_manager/modules/__init__.py`
- `src/stac_manager/modules/config.py`
- `src/stac_manager/modules/seed.py`
- `src/stac_manager/modules/update.py`

**Test Code:**
- `tests/fixtures/context.py`
- `tests/fixtures/modules.py`
- `tests/unit/core/test_context.py`
- `tests/unit/test_protocols.py`
- `tests/unit/modules/test_config.py`
- `tests/unit/modules/test_seed.py`
- `tests/unit/modules/test_update.py`

### Verification Commands

**Run all Part 1 tests:**
```bash
pytest tests/unit/core/ tests/unit/modules/ tests/unit/test_protocols.py -v
```

**Expected**: All 17 tasks' tests passing

**Check protocol compliance:**
```bash
# Type checking (requires mypy)
mypy src/stac_manager/core/ src/stac_manager/modules/ --strict
```

**Coverage check:**
```bash
pytest tests/unit/ --cov=src/stac_manager/core --cov=src/stac_manager/modules --cov-report=term-missing
```

**Expected**: ≥90% coverage

---

## Next Steps

**Part 1 is complete and ready for execution!**

Before proceeding to Part 2, you can:

1. **Execute Part 1** using the `executing-plans` or `subagent-driven-development` skill
2. **Review Part 1** for any adjustments
3. **Approve** for me to create detailed Part 2 & Part 3 specifications

**Parts 2 & 3 will cover:**

### Part 2: Complex Modifiers (Tasks 18-35)
- ValidateModule (stac-validator integration)
- ExtensionModule (JSON Schema scaffolding)
- TransformModule (sidecar enrichment, field mapping)

### Part 3: I/O & Integration (Tasks 36-56)
- IngestModule (API/File fetching, parallelism)
- OutputModule (JSON/Parquet output)
- Integration tests and end-to-end verification

**Would you like me to create skeleton outlines for Parts 2 & 3 now?**

