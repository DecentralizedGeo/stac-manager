# Comprehensive Logging Enhancement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enhance STAC Manager's logging system with per-step log levels, improved formatting (short paths), structured INFO/DEBUG messages, and comprehensive instrumentation across all modules.

**Architecture:** Pipe-and-filter pattern with logger injection. Each module receives a step-specific logger from the orchestrator, enabling granular control. Logging follows a two-tier approach: INFO for operational visibility (summaries), DEBUG for diagnostic detail (field-level operations).

**Tech Stack:** Python 3.12+, logging module, ShortPathFilter, Pydantic config models

---

## Table of Contents

- [Phase 1: Infrastructure (Completed ✅)](#phase-1-infrastructure-completed-)
- [Phase 2: UpdateModule Prototype (Completed ✅)](#phase-2-updatemodule-prototype-completed-)
- [Phase 3: Fix Logger Level Inheritance (Completed ✅)](#phase-3-fix-logger-level-inheritance-completed-)
- [Phase 4: Remaining Modules (20 tasks)](#phase-4-remaining-modules-20-tasks)
- [Phase 5: Documentation & Validation (6 tasks)](#phase-5-documentation--validation-6-tasks)

**Total Tasks**: 26 (5 modules × 4 tasks each + 6 validation tasks)

---

## Phase 1: Infrastructure (Completed ✅)

### Summary
Successfully implemented logging infrastructure improvements including ShortPathFilter, SystemExit bug fix, and per-step log level configuration.

### Key Deliverables
1. **ShortPathFilter** (`src/stac_manager/utils/logging.py:12-52`)
   - Converts full Windows paths to readable module notation
   - Example: `C:\...\stac-manager\src\stac_manager\modules\update.py` → `modules.update`

2. **SystemExit Fix** (`src/stac_manager/utils/logging.py:188-271`)
   - Correctly distinguishes exit code 0 (success) from non-zero (failure)
   - No more misleading ERROR messages for successful workflows

3. **StepConfig Enhancement** (`src/stac_manager/core/config.py:9-17`)
   - Added `log_level` field to `StepConfig` for per-step overrides
   - Optional field with validation

4. **Enhanced setup_logger** (`src/stac_manager/utils/logging.py:102-185`)
   - Configurable output format (text/json)
   - ShortPathFilter applied to all handlers
   - Progress interval support

### Test Coverage
- All existing 209 tests passing
- Infrastructure changes backward compatible

---

## Phase 2: UpdateModule Prototype (Completed ✅)

### Summary
Validated logging pattern with full UpdateModule instrumentation. Confirmed logger injection, INFO/DEBUG message structure, and integration with StacManager.

### Key Deliverables
1. **Logger Injection** (`src/stac_manager/modules/update.py:33-40`)
   ```python
   def set_logger(self, logger: logging.Logger) -> None:
       """Set step-specific logger for this module."""
       self.logger = logger
   ```

2. **INFO-Level Logging** (`src/stac_manager/modules/update.py:90, 160`)
   - Field removal summaries with counts and patterns
   - Update summaries with change counts
   - Example: `Removed fields | item: LC09... | count: 24 | patterns: ['assets.*.alternate']`

3. **DEBUG-Level Logging** (`src/stac_manager/modules/update.py:60, 83, 140`)
   - Processing item announcements
   - Field-level removal details
   - Individual field updates with values
   - Example: `Removed field | item: LC09... | path: assets.SAA.alternate`

### Validation
- Manual testing with `landsat-dgeo-migration.yaml`
- Console output shows short paths, structured messages
- Step-specific logger hierarchy working: `stac_manager.landsat-dgeo-migration.remove_old_alternates`

---

## Phase 3: Fix Logger Level Inheritance (Completed ✅)

### Summary
Fixed critical bug where StacManager was using CLI default (INFO) instead of YAML-configured DEBUG level.

### Key Changes
1. **StacManager.__init__** (`src/stac_manager/core/manager.py:98-126`)
   - Now reads log level from `workflow.settings.logging.level`
   - Falls back to CLI parameter if not in workflow config
   - Properly inherits DEBUG from YAML

2. **Step Logger Injection** (`src/stac_manager/core/manager.py:154-180`)
   - Creates step-specific loggers with hierarchical names
   - Inherits parent level when no step override specified
   - Injects via `set_logger()` if module supports it

### Test Updates
- Fixed `test_update_module_logs_operations` to inject logger
- Fixed `test_run_workflow_uses_log_context_and_json_file` to check `logger` field instead of deprecated `step_id`
- All 209 tests passing

---

## Phase 4: Remaining Modules (20 tasks)

### Module Instrumentation Order
1. IngestModule (Tasks 1-4)
2. TransformModule (Tasks 5-8)
3. ExtensionModule (Tasks 9-12)
4. OutputModule (Tasks 13-16)
5. ValidateModule (Tasks 17-20)

**Pattern for Each Module:**
- Task N.1: Add `set_logger()` method + Write failing test
- Task N.2: Add INFO-level logging + Verify test passes
- Task N.3: Add DEBUG-level logging + Write additional test + Verify
- Task N.4: Integration test + Commit

---

### Task 1: IngestModule - Logger Injection

**Files:**
- Modify: `src/stac_manager/modules/ingest.py:__init__`
- Test: `tests/unit/modules/test_logging_instrumentation.py`

**Step 1: Write failing test**

Add to `tests/unit/modules/test_logging_instrumentation.py` after existing tests:

```python
@pytest.mark.asyncio
async def test_ingest_module_accepts_injected_logger():
    """Test IngestModule has set_logger method and uses it."""
    mock_logger = MagicMock(spec=logging.Logger)
    context = MockWorkflowContext.create()
    
    config = {"mode": "file", "source": "items.json", "format": "json"}
    
    with patch('pathlib.Path.exists', return_value=True):
        module = IngestModule(config)
        
        # Module should have set_logger method
        assert hasattr(module, 'set_logger'), "IngestModule missing set_logger method"
        
        # Inject logger
        module.set_logger(mock_logger)
        
        # Verify logger was set
        assert module.logger is mock_logger
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/modules/test_logging_instrumentation.py::test_ingest_module_accepts_injected_logger -v
```

Expected: `FAIL` with "IngestModule missing set_logger method"

**Step 3: Write minimal implementation**

In `src/stac_manager/modules/ingest.py`, add after `__init__` method:

```python
def set_logger(self, logger: logging.Logger) -> None:
    """Set step-specific logger for this module."""
    self.logger = logger
```

Also update `__init__` to initialize default logger:

```python
def __init__(self, config: dict):
    self.config = IngestConfig(**config)
    self.logger = logging.getLogger(__name__)  # Default logger
    # ... rest of init
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/modules/test_logging_instrumentation.py::test_ingest_module_accepts_injected_logger -v
```

Expected: `PASS`

**Step 5: Commit**

```bash
git add src/stac_manager/modules/ingest.py tests/unit/modules/test_logging_instrumentation.py
git commit -m "feat(logging): add logger injection to IngestModule"
```

---

### Task 2: IngestModule - INFO-Level Logging

**Files:**
- Modify: `src/stac_manager/modules/ingest.py:fetch()`
- Test: `tests/unit/modules/test_logging_instrumentation.py`

**Step 1: Write failing test**

```python
@pytest.mark.asyncio
async def test_ingest_module_logs_info_messages():
    """Test IngestModule logs INFO-level summaries."""
    mock_logger = MagicMock(spec=logging.Logger)
    context = MockWorkflowContext.create()
    
    config = {"mode": "file", "source": "items.json", "format": "json"}
    
    with patch('stac_manager.modules.ingest.IngestModule._load_json_file') as mock_load:
        async def async_gen(_):
            yield {"id": "item-1"}
            yield {"id": "item-2"}
        mock_load.return_value = async_gen(None)
        
        with patch('pathlib.Path.exists', return_value=True):
            module = IngestModule(config)
            module.set_logger(mock_logger)
            
            # Fetch items
            items = [item async for item in module.fetch(context)]
            
            # Verify INFO logs
            info_calls = [str(args[0]) for args, _ in mock_logger.info.call_args_list]
            
            # Should log start of ingest
            assert any("Starting ingest" in call for call in info_calls), \
                f"Expected 'Starting ingest' in INFO logs, got: {info_calls}"
            
            # Should log completion with count
            assert any("Ingest complete" in call and "total_items: 2" in call for call in info_calls), \
                f"Expected 'Ingest complete | total_items: 2' in INFO logs, got: {info_calls}"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/modules/test_logging_instrumentation.py::test_ingest_module_logs_info_messages -v
```

Expected: `FAIL` with "Expected 'Starting ingest' in INFO logs"

**Step 3: Write minimal implementation**

In `src/stac_manager/modules/ingest.py`, modify `fetch()` method:

```python
async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
    """Fetch STAC items from configured source."""
    # Log start
    self.logger.info(
        f"Starting ingest | mode: {self.config.mode} | source: {self.config.source}"
    )
    
    count = 0
    
    if self.config.mode == "api":
        async for item in self._fetch_from_api(context):
            count += 1
            yield item
    elif self.config.mode == "file":
        async for item in self._fetch_from_file(context):
            count += 1
            yield item
    
    # Log completion
    self.logger.info(f"Ingest complete | total_items: {count}")
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/modules/test_logging_instrumentation.py::test_ingest_module_logs_info_messages -v
```

Expected: `PASS`

**Step 5: Commit**

```bash
git add src/stac_manager/modules/ingest.py tests/unit/modules/test_logging_instrumentation.py
git commit -m "feat(logging): add INFO-level logging to IngestModule"
```

---

### Task 3: IngestModule - DEBUG-Level Logging

**Files:**
- Modify: `src/stac_manager/modules/ingest.py:fetch()`
- Test: `tests/unit/modules/test_logging_instrumentation.py`

**Step 1: Write failing test**

```python
@pytest.mark.asyncio
async def test_ingest_module_logs_debug_details():
    """Test IngestModule logs DEBUG-level item details."""
    mock_logger = MagicMock(spec=logging.Logger)
    context = MockWorkflowContext.create()
    
    config = {"mode": "file", "source": "items.json", "format": "json"}
    
    with patch('stac_manager.modules.ingest.IngestModule._load_json_file') as mock_load:
        async def async_gen(_):
            yield {"id": "test-item-1", "collection": "test-collection"}
            yield {"id": "test-item-2", "collection": "test-collection"}
        mock_load.return_value = async_gen(None)
        
        with patch('pathlib.Path.exists', return_value=True):
            module = IngestModule(config)
            module.set_logger(mock_logger)
            
            items = [item async for item in module.fetch(context)]
            
            # Verify DEBUG logs
            debug_calls = [str(args[0]) for args, _ in mock_logger.debug.call_args_list]
            
            # Should log each fetched item
            assert any("test-item-1" in call for call in debug_calls), \
                f"Expected 'test-item-1' in DEBUG logs, got: {debug_calls}"
            assert any("test-item-2" in call for call in debug_calls), \
                f"Expected 'test-item-2' in DEBUG logs, got: {debug_calls}"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/modules/test_logging_instrumentation.py::test_ingest_module_logs_debug_details -v
```

Expected: `FAIL` with "Expected 'test-item-1' in DEBUG logs"

**Step 3: Write minimal implementation**

In `src/stac_manager/modules/ingest.py`, enhanced `fetch()` method:

```python
async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
    """Fetch STAC items from configured source."""
    self.logger.info(
        f"Starting ingest | mode: {self.config.mode} | source: {self.config.source}"
    )
    
    count = 0
    progress_interval = 100  # Log progress every 100 items
    
    if self.config.mode == "api":
        async for item in self._fetch_from_api(context):
            count += 1
            item_id = item.get('id', 'unknown')
            
            # DEBUG: Log each item
            self.logger.debug(f"Fetched item | item: {item_id} | count: {count}")
            
            # INFO: Progress logging
            if count % progress_interval == 0:
                self.logger.info(f"Ingest progress | items_fetched: {count}")
            
            yield item
            
    elif self.config.mode == "file":
        async for item in self._fetch_from_file(context):
            count += 1
            item_id = item.get('id', 'unknown')
            
            # DEBUG: Log each item
            self.logger.debug(f"Fetched item | item: {item_id} | count: {count}")
            
            # INFO: Progress logging
            if count % progress_interval == 0:
                self.logger.info(f"Ingest progress | items_fetched: {count}")
            
            yield item
    
    self.logger.info(f"Ingest complete | total_items: {count}")
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/modules/test_logging_instrumentation.py::test_ingest_module_logs_debug_details -v
```

Expected: `PASS`

**Step 5: Commit**

```bash
git add src/stac_manager/modules/ingest.py tests/unit/modules/test_logging_instrumentation.py
git commit -m "feat(logging): add DEBUG-level logging to IngestModule"
```

---

### Task 4: IngestModule - Integration Test + Full Validation

**Files:**
- Test: `tests/integration/test_module_logging.py` (NEW)
- Run: Full test suite validation

**Step 1: Write integration test**

Create `tests/integration/test_module_logging.py`:

```python
"""Integration tests for module logging."""
import pytest
import logging
from unittest.mock import MagicMock
from stac_manager.modules.ingest import IngestModule
from tests.fixtures.context import MockWorkflowContext


@pytest.mark.asyncio
async def test_ingest_module_logging_integration():
    """Test IngestModule logging in realistic scenario."""
    # Create real logger for integration test
    logger = logging.getLogger("test.ingest_module")
    logger.setLevel(logging.DEBUG)
    
    # Capture log messages
    captured_logs = []
    
    class LogCapture(logging.Handler):
        def emit(self, record):
            captured_logs.append({
                "level": record.levelname,
                "message": record.getMessage(),
            })
    
    handler = LogCapture()
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    # Create config and module
    config = {
        "mode": "file",
        "source": "tests/fixtures/data/sample-items.json",
        "format": "json"
    }
    
    module = IngestModule(config)
    module.set_logger(logger)
    
    context = MockWorkflowContext.create()
    
    # Fetch items
    items = [item async for item in module.fetch(context)]
    
    # Verify log structure
    info_logs = [log for log in captured_logs if log["level"] == "INFO"]
    debug_logs = [log for log in captured_logs if log["level"] == "DEBUG"]
    
    # Should have INFO for start and complete
    assert len(info_logs) >= 2, "Expected at least 2 INFO logs (start, complete)"
    
    # Should have DEBUG for each item
    assert len(debug_logs) >= len(items), \
        f"Expected at least {len(items)} DEBUG logs, got {len(debug_logs)}"
    
    # Verify message structure (pipe-separated)
    start_log = info_logs[0]["message"]
    assert "|" in start_log, "INFO messages should use pipe separators"
    assert "Starting ingest" in start_log
```

**Step 2: Run integration test**

```bash
pytest tests/integration/test_module_logging.py::test_ingest_module_logging_integration -v
```

Expected: `PASS`

**Step 3: Run full test suite**

```bash
pytest tests/ -v --tb=short
```

Expected: All tests pass (209+ with new tests)

**Step 4: Commit**

```bash
git add tests/integration/test_module_logging.py
git commit -m "test(logging): add IngestModule logging integration test"
```

---

### Task 5: TransformModule - Logger Injection

**Files:**
- Modify: `src/stac_manager/modules/transform.py:__init__`
- Test: `tests/unit/modules/test_logging_instrumentation.py`

**Step 1: Write failing test**

```python
@pytest.mark.asyncio
async def test_transform_module_accepts_injected_logger():
    """Test TransformModule has set_logger method and uses it."""
    mock_logger = MagicMock(spec=logging.Logger)
    context = MockWorkflowContext.create()
    
    config = {
        "input_file": "test.csv",
        "input_join_key": "id",
        "field_mapping": {"properties.test": "value"}
    }
    
    with patch('pathlib.Path.exists', return_value=True), \
         patch('stac_manager.modules.transform.TransformModule._load_csv') as mock_load:
        mock_load.return_value = {}
        
        module = TransformModule(config)
        
        # Module should have set_logger method
        assert hasattr(module, 'set_logger'), "TransformModule missing set_logger method"
        
        # Inject logger
        module.set_logger(mock_logger)
        
        # Verify logger was set
        assert module.logger is mock_logger
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/modules/test_logging_instrumentation.py::test_transform_module_accepts_injected_logger -v
```

Expected: `FAIL` with "TransformModule missing set_logger method"

**Step 3: Write minimal implementation**

In `src/stac_manager/modules/transform.py`:

```python
def __init__(self, config: dict):
    self.config = TransformConfig(**config)
    self.logger = logging.getLogger(__name__)  # Default logger
    # ... rest of init

def set_logger(self, logger: logging.Logger) -> None:
    """Set step-specific logger for this module."""
    self.logger = logger
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/modules/test_logging_instrumentation.py::test_transform_module_accepts_injected_logger -v
```

Expected: `PASS`

**Step 5: Commit**

```bash
git add src/stac_manager/modules/transform.py tests/unit/modules/test_logging_instrumentation.py
git commit -m "feat(logging): add logger injection to TransformModule"
```

---

### Task 6: TransformModule - INFO-Level Logging

**Files:**
- Modify: `src/stac_manager/modules/transform.py:modify()`
- Test: `tests/unit/modules/test_logging_instrumentation.py`

**Step 1: Write failing test**

```python
@pytest.mark.asyncio
async def test_transform_module_logs_enrichment():
    """Test TransformModule logs enrichment INFO messages."""
    mock_logger = MagicMock(spec=logging.Logger)
    context = MockWorkflowContext.create()
    
    config = {
        "input_file": "test.csv",
        "input_join_key": "id",
        "field_mapping": {"properties.cloud_cover": "cloud_cover"}
    }
    
    with patch('pathlib.Path.exists', return_value=True), \
         patch('stac_manager.modules.transform.TransformModule._load_csv'):
        module = TransformModule(config)
        module.set_logger(mock_logger)
        
        # Set up test data
        module.input_index = {"test-item": {"cloud_cover": 42}}
        
        item = {"id": "test-item", "properties": {}}
        result = module.modify(item, context)
        
        # Verify INFO logs
        info_calls = [str(args[0]) for args, _ in mock_logger.info.call_args_list]
        
        assert any("Enriched item" in call and "test-item" in call for call in info_calls), \
            f"Expected 'Enriched item' with 'test-item' in INFO logs, got: {info_calls}"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/modules/test_logging_instrumentation.py::test_transform_module_logs_enrichment -v
```

Expected: `FAIL`

**Step 3: Write minimal implementation**

In `src/stac_manager/modules/transform.py`, modify `modify()` method:

```python
def modify(self, item: dict, context: WorkflowContext) -> dict:
    """Enrich item with input data."""
    item_id = item.get('id', 'unknown')
    
    # Find matching input data
    join_value = get_nested_field(item, self.config.input_join_key)
    matching_data = self.input_index.get(join_value)
    
    if not matching_data:
        self.logger.warning(
            f"No match found | item: {item_id} | join_key: {join_value}"
        )
        return item
    
    # Apply field mappings
    mapped_count = 0
    # ... (existing mapping logic)
    
    # Log enrichment summary
    self.logger.info(
        f"Enriched item | item: {item_id} | fields_mapped: {mapped_count} | "
        f"strategy: {self.config.strategy}"
    )
    
    return item
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/modules/test_logging_instrumentation.py::test_transform_module_logs_enrichment -v
```

Expected: `PASS`

**Step 5: Commit**

```bash
git add src/stac_manager/modules/transform.py tests/unit/modules/test_logging_instrumentation.py
git commit -m "feat(logging): add INFO-level logging to TransformModule"
```

---

### Task 7: TransformModule - DEBUG-Level Logging

**Files:**
- Modify: `src/stac_manager/modules/transform.py:modify()`
- Test: `tests/unit/modules/test_logging_instrumentation.py`

**Step 1: Write failing test**

```python
@pytest.mark.asyncio
async def test_transform_module_logs_debug_field_mappings():
    """Test TransformModule logs DEBUG-level field mapping details."""
    mock_logger = MagicMock(spec=logging.Logger)
    context = MockWorkflowContext.create()
    
    config = {
        "input_file": "test.csv",
        "input_join_key": "id",
        "field_mapping": {"properties.cloud_cover": "cloud_cover"}
    }
    
    with patch('pathlib.Path.exists', return_value=True), \
         patch('stac_manager.modules.transform.TransformModule._load_csv'):
        module = TransformModule(config)
        module.set_logger(mock_logger)
        module.input_index = {"test-item": {"cloud_cover": 42}}
        
        item = {"id": "test-item", "properties": {}}
        result = module.modify(item, context)
        
        # Verify DEBUG logs
        debug_calls = [str(args[0]) for args, _ in mock_logger.debug.call_args_list]
        
        # Should log field mapping details
        assert any("Mapped field" in call and "properties.cloud_cover" in call for call in debug_calls), \
            f"Expected 'Mapped field' with target path in DEBUG logs, got: {debug_calls}"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/modules/test_logging_instrumentation.py::test_transform_module_logs_debug_field_mappings -v
```

Expected: `FAIL`

**Step 3: Write minimal implementation**

In `src/stac_manager/modules/transform.py`:

```python
def modify(self, item: dict, context: WorkflowContext) -> dict:
    """Enrich item with input data."""
    item_id = item.get('id', 'unknown')
    
    # DEBUG: Processing item
    self.logger.debug(f"Processing item | item: {item_id}")
    
    # Find matching input data
    join_value = get_nested_field(item, self.config.input_join_key)
    matching_data = self.input_index.get(join_value)
    
    if not matching_data:
        self.logger.warning(f"No match found | item: {item_id} | join_key: {join_value}")
        return item
    
    # DEBUG: Match found
    self.logger.debug(f"Matched input data | item: {item_id} | join_value: {join_value}")
    
    # Apply field mappings
    mapped_count = 0
    for target_path, source_expr in self.config.field_mapping.items():
        value = self._extract_value(matching_data, source_expr)
        set_nested_field(item, target_path, value)
        mapped_count += 1
        
        # DEBUG: Individual field mapping
        self.logger.debug(
            f"Mapped field | item: {item_id} | target: {target_path} | "
            f"source: {source_expr} | value: {value}"
        )
    
    # INFO: Enrichment summary
    self.logger.info(
        f"Enriched item | item: {item_id} | fields_mapped: {mapped_count} | "
        f"strategy: {self.config.strategy}"
    )
    
    return item
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/modules/test_logging_instrumentation.py::test_transform_module_logs_debug_field_mappings -v
```

Expected: `PASS`

**Step 5: Commit**

```bash
git add src/stac_manager/modules/transform.py tests/unit/modules/test_logging_instrumentation.py
git commit -m "feat(logging): add DEBUG-level logging to TransformModule"
```

---

### Task 8: TransformModule - Integration Test

**Files:**
- Test: `tests/integration/test_module_logging.py`

**Step 1: Write integration test**

Add to `tests/integration/test_module_logging.py`:

```python
@pytest.mark.asyncio
async def test_transform_module_logging_integration():
    """Test TransformModule logging in realistic scenario."""
    logger = logging.getLogger("test.transform_module")
    logger.setLevel(logging.DEBUG)
    
    captured_logs = []
    
    class LogCapture(logging.Handler):
        def emit(self, record):
            captured_logs.append({
                "level": record.levelname,
                "message": record.getMessage(),
            })
    
    handler = LogCapture()
    logger.addHandler(handler)
    
    config = {
        "input_file": "tests/fixtures/data/sample-metadata.csv",
        "input_join_key": "id",
        "field_mapping": {"properties.cloud_cover": "cloud_cover"}
    }
    
    module = TransformModule(config)
    module.set_logger(logger)
    
    context = MockWorkflowContext.create()
    
    # Process test item
    item = {"id": "test-item", "properties": {}}
    result = module.modify(item, context)
    
    # Verify log structure
    info_logs = [log for log in captured_logs if log["level"] == "INFO"]
    debug_logs = [log for log in captured_logs if log["level"] == "DEBUG"]
    
    assert len(info_logs) >= 1, "Expected INFO enrichment summary"
    assert len(debug_logs) >= 1, "Expected DEBUG field mapping details"
```

**Step 2: Run test**

```bash
pytest tests/integration/test_module_logging.py::test_transform_module_logging_integration -v
```

Expected: `PASS`

**Step 3: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests pass

**Step 4: Commit**

```bash
git add tests/integration/test_module_logging.py
git commit -m "test(logging): add TransformModule logging integration test"
```

---

### Task 9: ExtensionModule - Logger Injection

**Files:**
- Modify: `src/stac_manager/modules/extension.py:__init__`
- Test: `tests/unit/modules/test_logging_instrumentation.py`

**Step 1: Write failing test**

```python
@pytest.mark.asyncio
async def test_extension_module_accepts_injected_logger():
    """Test ExtensionModule has set_logger method."""
    mock_logger = MagicMock(spec=logging.Logger)
    
    config = {
        "uri": "https://stac-extensions.github.io/projection/v1.1.0/schema.json"
    }
    
    with patch('requests.get'):
        module = ExtensionModule(config)
        
        assert hasattr(module, 'set_logger'), "ExtensionModule missing set_logger method"
        module.set_logger(mock_logger)
        assert module.logger is mock_logger
```

**Step 2-5: Same pattern as previous modules**

---

### Task 10: ExtensionModule - INFO-Level Logging

**Files:**
- Modify: `src/stac_manager/modules/extension.py:modify()`
- Test: `tests/unit/modules/test_logging_instrumentation.py`

**Implementation:**

```python
def modify(self, item: dict, context: WorkflowContext) -> dict:
    """Apply extension to item."""
    item_id = item.get('id', 'unknown')
    
    # Add extension URI
    if self.extension_uri not in item.get('stac_extensions', []):
        item.setdefault('stac_extensions', []).append(self.extension_uri)
        self.logger.info(f"Added extension | item: {item_id} | uri: {self.extension_uri}")
    
    # Apply defaults
    if self.config.defaults:
        applied_count = len(self.config.defaults)
        # ... apply defaults ...
        self.logger.info(f"Applied defaults | item: {item_id} | count: {applied_count}")
    
    return item
```

---

### Task 11: ExtensionModule - DEBUG-Level Logging

**Implementation:**

```python
def modify(self, item: dict, context: WorkflowContext) -> dict:
    """Apply extension to item."""
    item_id = item.get('id', 'unknown')
    
    self.logger.debug(f"Processing item | item: {item_id}")
    
    # Add extension URI
    if self.extension_uri not in item.get('stac_extensions', []):
        item.setdefault('stac_extensions', []).append(self.extension_uri)
        self.logger.info(f"Added extension | item: {item_id} | uri: {self.extension_uri}")
    
    # Apply defaults
    if self.config.defaults:
        for path, value in expanded_defaults.items():
            self.logger.debug(
                f"Applied default | item: {item_id} | path: {path} | value: {value}"
            )
            # ... apply ...
        
        self.logger.info(f"Applied defaults | item: {item_id} | count: {len(expanded_defaults)}")
    
    return item
```

---

### Task 12: ExtensionModule - Integration Test

Similar pattern to other modules.

---

### Task 13: OutputModule - Logger Injection

**Files:**
- Modify: `src/stac_manager/modules/output.py:__init__`
- Test: `tests/unit/modules/test_logging_instrumentation.py`

**Implementation:**

```python
def __init__(self, config: dict):
    self.config = OutputConfig(**config)
    self.logger = logging.getLogger(__name__)
    # ... rest

def set_logger(self, logger: logging.Logger) -> None:
    """Set step-specific logger for this module."""
    self.logger = logger
```

---

### Task 14: OutputModule - INFO-Level Logging

**Implementation:**

```python
async def bundle(self, item: dict, context: WorkflowContext) -> None:
    """Buffer item for output."""
    self.buffer.append(item)
    
    if len(self.buffer) >= self.config.buffer_size:
        self.logger.info(
            f"Auto-flush triggered | buffered: {len(self.buffer)} | "
            f"total_written: {self.items_written}"
        )
        await self._flush(context)

async def _flush_json(self, context: WorkflowContext) -> None:
    """Flush JSON items to disk."""
    item_count = len(self.buffer)
    # ... write logic ...
    
    self.logger.info(
        f"Flushed to disk | format: json | items: {item_count} | path: {items_dir}"
    )
```

---

### Task 15: OutputModule - DEBUG-Level Logging

**Implementation:**

```python
async def bundle(self, item: dict, context: WorkflowContext) -> None:
    """Buffer item for output."""
    item_id = item.get('id', 'unknown')
    
    self.buffer.append(item)
    self.logger.debug(
        f"Buffered item | item: {item_id} | buffer_size: {len(self.buffer)}/{self.config.buffer_size}"
    )
    
    if len(self.buffer) >= self.config.buffer_size:
        self.logger.info(
            f"Auto-flush triggered | buffered: {len(self.buffer)} | total_written: {self.items_written}"
        )
        await self._flush(context)
```

---

### Task 16: OutputModule - Integration Test

Similar pattern to other modules.

---

### Task 17: ValidateModule - Logger Injection

**Files:**
- Modify: `src/stac_manager/modules/validate.py:__init__`
- Test: `tests/unit/modules/test_logging_instrumentation.py`

**Implementation:**

```python
def __init__(self, config: dict):
    self.config = ValidateConfig(**config)
    self.logger = logging.getLogger(__name__)

def set_logger(self, logger: logging.Logger) -> None:
    """Set step-specific logger for this module."""
    self.logger = logger
```

---

### Task 18: ValidateModule - INFO-Level Logging

**Implementation:**

```python
def modify(self, item: dict, context: WorkflowContext) -> dict:
    """Validate STAC item."""
    item_id = item.get('id', 'unknown')
    
    errors = validate_item(item)
    
    if errors:
        if self.config.strict:
            self.logger.error(f"Validation failed | item: {item_id} | errors: {len(errors)}")
            context.failure_collector.add_failure(item_id, step_id, ValidationError(...))
        else:
            self.logger.warning(f"Validation warnings | item: {item_id} | errors: {len(errors)}")
    else:
        self.logger.info(f"Validation passed | item: {item_id}")
    
    return item
```

---

### Task 19: ValidateModule - DEBUG-Level Logging

**Implementation:**

```python
def modify(self, item: dict, context: WorkflowContext) -> dict:
    """Validate STAC item."""
    item_id = item.get('id', 'unknown')
    
    self.logger.debug(f"Validating item | item: {item_id}")
    
    errors = validate_item(item)
    
    if errors:
        for error in errors:
            self.logger.debug(f"Validation error | item: {item_id} | error: {error}")
        
        if self.config.strict:
            self.logger.error(f"Validation failed | item: {item_id} | errors: {len(errors)}")
        else:
            self.logger.warning(f"Validation warnings | item: {item_id} | errors: {len(errors)}")
    else:
        self.logger.info(f"Validation passed | item: {item_id}")
    
    return item
```

---

### Task 20: ValidateModule - Integration Test

Similar pattern to other modules.

---

## Phase 5: Documentation & Validation (6 tasks)

### Task 21: Update Agent Memory

**Files:**
- Update: `.agent/memory/episodic.md`
- Update: `.agent/memory/procedural.md`
- Update: `.agent/memory/semantic.md`

**Step 1: Document logging patterns in procedural.md**

Add new section:

```markdown
## Module Logging Patterns (v1.1.0)

### Logger Injection
- **Pattern**: All modules must implement `set_logger(logger)` method
- **Default Logger**: Initialize `self.logger = logging.getLogger(__name__)` in `__init__`
- **Injection**: StacManager calls `module.set_logger(step_logger)` during instantiation
- **Hierarchy**: Step loggers named `stac_manager.{workflow_name}.{step_id}`

### Message Structure
- **Format**: `{operation} | key: value | key: value`
- **Separators**: Use pipe `|` for readability in console output
- **Item ID**: Always include `item: {item_id}` in item-processing logs

### Logging Levels
- **INFO**: Operational summaries (counts, status changes)
  - Example: `Enriched item | item: LC09... | fields_mapped: 24`
- **DEBUG**: Field-level diagnostics (individual operations)
  - Example: `Mapped field | item: LC09... | target: properties.cloud_cover | value: 42`

### Per-Step Configuration
- **YAML Config**: Add `log_level: DEBUG` to step config for override
- **Inheritance**: Steps without explicit level inherit global `settings.logging.level`
- **Override Priority**: Step-level > Global level > CLI default (INFO)
```

**Step 2: Document infrastructure in semantic.md**

```markdown
## Logging Infrastructure (v1.1.0)

### ShortPathFilter
- **Location**: `stac_manager.utils.logging.ShortPathFilter`
- **Purpose**: Convert full file paths to readable module notation
- **Example**: `C:\...\src\stac_manager\modules\update.py` → `modules.update`
- **Applied**: Both console and file handlers

### Logger Hierarchy
- **Root**: `stac_manager`
- **Workflow**: `stac_manager.{workflow_name}`
- **Step**: `stac_manager.{workflow_name}.{step_id}`
- **Benefit**: Granular filtering with logger name patterns

### Configuration Options
- **Global Level**: `settings.logging.level` (DEBUG, INFO, WARNING, ERROR)
- **Output Format**: `settings.logging.output_format` (text, json)
- **Progress Interval**: `settings.logging.progress_interval` (default: 100)
- **File Path**: `settings.logging.file` (default: logs/stac_manager.log)
```

**Step 3: Commit**

```bash
git add .agent/memory/*.md
git commit -m "docs(memory): document logging patterns and infrastructure"
```

---

### Task 22: Create User Documentation

**Files:**
- Create: `docs/user-guide/logging.md`

**Step 1: Write logging guide**

Create comprehensive user guide covering:
- Per-step log level configuration
- Message structure and interpretation
- Filtering logs by step or module
- JSON vs text format selection
- Progress interval customization

**Step 2: Update docs index**

Add link to logging guide in `docs/user-guide/README.md`

**Step 3: Commit**

```bash
git add docs/user-guide/logging.md docs/user-guide/README.md
git commit -m "docs: add comprehensive logging configuration guide"
```

---

### Task 23: End-to-End Workflow Test

**Files:**
- Test: Manual validation with `examples/landsat-dgeo-migration.yaml`

**Step 1: Run with INFO level**

```bash
stac-manager run-workflow examples/landsat-dgeo-migration.yaml
```

**Verify:**
- Short paths in console output
- INFO summaries for all modules
- No DEBUG messages
- Correct success message (not ERROR)

**Step 2: Run with DEBUG on specific step**

Edit `landsat-dgeo-migration.yaml`:
```yaml
- id: remove_old_alternates
  module: UpdateModule
  log_level: DEBUG  # Add this
  config:
    removes:
      - "assets.*.alternate"
```

Run: `stac-manager run-workflow examples/landsat-dgeo-migration.yaml`

**Verify:**
- DEBUG messages appear for `remove_old_alternates` only
- Field-level details visible
- Other steps show INFO only

**Step 3: Run with JSON format**

Edit workflow:
```yaml
settings:
  logging:
    level: DEBUG
    output_format: json
    file: logs/stac_manager.json
```

Run and verify JSON format:
```bash
cat logs/stac_manager.json | jq '.' | head -20
```

**Step 4: Document results in walkthrough**

Update walkthrough.md with validation results.

---

### Task 24: Performance Benchmark

**Files:**
- Script: `tests/performance/benchmark_logging.py` (NEW)

**Step 1: Create benchmark script**

```python
"""Benchmark logging performance impact."""
import time
import asyncio
from stac_manager import StacManager

async def benchmark_logging_levels():
    """Compare workflow execution time with different log levels."""
    
    results = {}
    
    for log_level in ['ERROR', 'WARNING', 'INFO', 'DEBUG']:
        config = {
            "name": "benchmark",
            "settings": {"logging": {"level": log_level}},
            "steps": [
                # ... large workflow ...
            ]
        }
        
        start = time.time()
        manager = StacManager(config)
        await manager.execute()
        duration = time.time() - start
        
        results[log_level] = duration
    
    return results

if __name__ == "__main__":
    results = asyncio.run(benchmark_logging_levels())
    for level, duration in results.items():
        print(f"{level}: {duration:.2f}s")
```

**Step 2: Run benchmark**

```bash
python tests/performance/benchmark_logging.py
```

**Step 3: Document findings**

If performance impact > 5%, investigate and optimize. Otherwise, document acceptable overhead.

---

### Task 25: Update Changelog

**Files:**
- Update: `CHANGELOG.md`

**Step 1: Add entry for v1.1.0**

```markdown
## [1.1.0] - 2026-01-30

### Added
- Comprehensive logging system with per-step log level control
- ShortPathFilter for readable module paths in log output
- Structured INFO/DEBUG messages across all modules
- Logger injection pattern for step-specific logging
- Support for JSON log format output
- Configurable progress interval logging

### Fixed
- SystemExit(0) no longer logged as ERROR (correct success detection)
- Logger level inheritance from workflow YAML configuration
- Step-specific loggers now properly inherit global log level

### Changed
- All modules now support `set_logger()` for logger injection
- Log messages use pipe-separated format for better readability
- JSON logs use `logger` field for step identification (removed `step_id`)

### Documentation
- Added comprehensive logging configuration guide
- Updated agent memory with logging patterns and best practices
```

**Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: update changelog for v1.1.0 logging enhancements"
```

---

### Task 26: Final Verification & Release Preparation

**Files:**
- Run: Complete test suite
- Run: All example workflows
- Review: All changed files

**Step 1: Run full test suite**

```bash
pytest tests/ -v --cov=stac_manager --cov-report=term-missing
```

**Verify:**
- All tests pass
- Coverage ≥ 90%
- No warnings in output

**Step 2: Run all example workflows**

```bash
for workflow in examples/*.yaml; do
    echo "Testing $workflow"
    stac-manager run-workflow "$workflow" || exit 1
done
```

**Verify:**
- All workflows execute successfully
- Logging output is readable and structured
- No errors or unexpected warnings

**Step 3: Code review checklist**

- [ ] All modules have `set_logger()` method
- [ ] INFO-level logging provides operational visibility
- [ ] DEBUG-level logging provides diagnostic detail
- [ ] Message format is consistent (pipe-separated)
- [ ] All tests pass
- [ ] Documentation is complete
- [ ] Agent memory is updated
- [ ] Changelog reflects all changes

**Step 4: Create release tag**

```bash
git tag -a v1.1.0 -m "Release v1.1.0: Comprehensive logging enhancements"
git push origin v1.1.0
```

---

## Verification Commands

After completing all tasks, verify the implementation:

### Test All Modules
```bash
pytest tests/unit/modules/test_logging_instrumentation.py -v
```

### Test Integration
```bash
pytest tests/integration/test_module_logging.py -v
```

### Full Test Suite
```bash
pytest tests/ -v --tb=short
```

### Manual Workflow Test
```bash
stac-manager run-workflow examples/landsat-dgeo-migration.yaml
```

---

## Success Criteria

✅ All 5 modules (IngestModule, TransformModule, ExtensionModule, OutputModule, ValidateModule) instrumented  
✅ Each module has `set_logger()` method  
✅ INFO-level logging provides operational summaries  
✅ DEBUG-level logging provides field-level diagnostics  
✅ All tests pass (209+ tests)  
✅ Per-step log level overrides work correctly  
✅ JSON format option works correctly  
✅ Documentation complete  
✅ Agent memory updated  
✅ Performance impact acceptable (<5% overhead)

---

## Notes

- **TDD Discipline**: ALWAYS write failing test first, watch it fail, then implement
- **Message Structure**: Use pipe separators consistently: `operation | key: value | key: value`
- **Item ID**: Always include `item: {item_id}` in item-processing logs
- **Logger Hierarchy**: Step loggers named `stac_manager.{workflow_name}.{step_id}`
- **Backward Compatibility**: Default logger in `__init__` ensures modules work without injection
- **Pattern Consistency**: Follow exact pattern from UpdateModule prototype
