# STAC Manager Utilities Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

> **Context**: This is **Phase 1: Utilities Foundation** of the STAC Manager implementation.  
> See [Implementation Roadmap](./2026-01-22-stac-manager-roadmap.md) for complete context.

**Goal**: Build the foundational utility layer (`stac_manager/utils/`) that will power STAC Manager's pipeline modules (Phase 2) and orchestration engine (Phase 3). These utilities provide PySTAC-based operations for field manipulation, geometry processing, streaming, and validation.

**Architecture**: Domain-Driven Modules (see [design doc](./2026-01-22-pystac-toolkit-design.md))
- `utils/serialization.py` - PySTAC ↔ dict conversion
- `utils/field_ops.py` - Nested field manipulation, JMESPath, deep_merge
- `utils/geometry.py` - Bbox calculation, geometry validation  
- `utils/streaming.py` - Async iterator utilities
- `utils/validation.py` - STAC validation, item hydration

**Tech Stack**: 
- Python 3.12+ (structural pattern matching, TypedDict)
- PySTAC 1.10+, PySTAC-Client 0.7+, JMESPath, Shapely 2.0+
- pytest, pytest-asyncio, pytest-cov

**Testing Philosophy**:
- TDD RED-GREEN-REFACTOR for every task
- No mocks on domain data (use real STAC items/geometries)
- Mock only infrastructure (HTTP, file I/O, WorkflowContext)
- ≥90% coverage including error paths

---

## Phase 1: Test Fixtures & Infrastructure

### Task 1: Create Test Fixtures

**Files:**
- Create: `tests/fixtures/__init__.py`
- Create: `tests/fixtures/stac_items.py`

**Step 1: Write fixture module with real STAC data**

Create `tests/fixtures/stac_items.py`:

```python
"""
Shared STAC test fixtures - real STAC data for testing.
No mocks on domain data.
"""

# Valid STAC 1.0.0 Item
VALID_ITEM = {
    "type": "Feature",
    "stac_version": "1.0.0",
    "id": "test-item-001",
    "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
    "bbox": [0.0, 0.0, 0.0, 0.0],
    "properties": {
        "datetime": "2024-01-01T00:00:00Z"
    },
    "assets": {},
    "links": []
}

# Partial item (for hydration tests)
PARTIAL_ITEM = {
    "id": "partial-001"
}

# Item with nested properties
NESTED_ITEM = {
    "type": "Feature",
    "stac_version": "1.0.0",
    "id": "nested-001",
    "geometry": None,
    "bbox": None,
    "properties": {
        "datetime": None,
        "instruments": ["OLI", "TIRS"],
        "eo:cloud_cover": 15.5
    },
    "assets": {},
    "links": []
}

# Invalid geometry (unclosed polygon)
INVALID_GEOMETRY = {
    "type": "Polygon",
    "coordinates": [[[0, 0], [1, 0], [1, 1]]]  # Missing closing coordinate
}

# Valid polygon geometry
VALID_POLYGON = {
    "type": "Polygon",
    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
}

# MultiPolygon
MULTI_POLYGON = {
    "type": "MultiPolygon",
    "coordinates": [
        [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
        [[[2, 2], [3, 2], [3, 3], [2, 3], [2, 2]]]
    ]
}
```

**Step 2: Commit**

```bash
git add tests/fixtures/stac_items.py tests/fixtures/__init__.py
git commit -m "test: add STAC test fixtures for utilities"
```

---

## Phase 2: Serialization Module (`utils/serialization.py`)

### Task 2: Serialization - Type Validation

**Files:**
- Create: `tests/unit/utils/test_serialization.py`
- Create: `stac_manager/utils/__init__.py`
- Create: `stac_manager/utils/serialization.py`

**Step 1: Write failing test for `ensure_dict()` with dict input**

Create `tests/unit/utils/test_serialization.py`:

```python
import pytest
import pystac
from stac_manager.utils.serialization import ensure_dict
from tests.fixtures.stac_items import VALID_ITEM


def test_ensure_dict_with_dict():
    """ensure_dict returns dict unchanged when given dict."""
    result = ensure_dict(VALID_ITEM)
    assert result == VALID_ITEM
    assert result is VALID_ITEM  # Same object
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/utils/test_serialization.py::test_ensure_dict_with_dict -v`  
Expected: FAIL with "ModuleNotFoundError: No module named 'stac_manager.utils.serialization'"

**Step 3: Write minimal implementation**

Create `stac_manager/utils/__init__.py`: (empty file)

Create `stac_manager/utils/serialization.py`:

```python
"""PySTAC ↔ dict serialization utilities."""
from typing import Union
import pystac


def ensure_dict(obj: Union[dict, pystac.STACObject]) -> dict:
    """
    Ensure input is a dict.
    
    Args:
        obj: dict or PySTAC object
        
    Returns:
        dict representation
    """
    if isinstance(obj, dict):
        return obj
    raise NotImplementedError("PySTAC object conversion not yet implemented")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/utils/test_serialization.py::test_ensure_dict_with_dict -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/utils/test_serialization.py stac_manager/utils/
git commit -m "feat(utils): add ensure_dict for dict input"
```

---

### Task 3: Serialization - PySTAC Object Support

**Files:**
- Modify: `tests/unit/utils/test_serialization.py`
- Modify: `stac_manager/utils/serialization.py`

**Step 1: Write failing test for `ensure_dict()` with PySTAC Item**

Add to `tests/unit/utils/test_serialization.py`:

```python
def test_ensure_dict_with_pystac_item():
    """ensure_dict converts PySTAC Item to dict."""
    item = pystac.Item.from_dict(VALID_ITEM)
    result = ensure_dict(item)
    
    assert isinstance(result, dict)
    assert result["id"] == "test-item-001"
    assert result["type"] == "Feature"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/utils/test_serialization.py::test_ensure_dict_with_pystac_item -v`  
Expected: FAIL with "NotImplementedError: PySTAC object conversion not yet implemented"

**Step 3: Implement PySTAC object handling**

Update `stac_manager/utils/serialization.py`:

```python
def ensure_dict(obj: Union[dict, pystac.STACObject]) -> dict:
    """Ensure input is a dict."""
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, pystac.STACObject):
        return obj.to_dict()
    raise TypeError(f"Expected dict or PySTAC object, got {type(obj)}")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/utils/test_serialization.py::test_ensure_dict_with_pystac_item -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/utils/test_serialization.py stac_manager/utils/serialization.py
git commit -m "feat(utils): add PySTAC object support to ensure_dict"
```

---

### Task 4: Serialization - from_dict with Auto-Detection

**Files:**
- Modify: `tests/unit/utils/test_serialization.py`
- Modify: `stac_manager/utils/serialization.py`

**Step 1: Write failing test for `from_dict()` with Item**

Add to `tests/unit/utils/test_serialization.py`:

```python
def test_from_dict_with_item():
    """from_dict creates PySTAC Item from dict."""
    result = from_dict(VALID_ITEM)
    
    assert isinstance(result, pystac.Item)
    assert result.id == "test-item-001"
    assert result.geometry == VALID_ITEM["geometry"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/utils/test_serialization.py::test_from_dict_with_item -v`  
Expected: FAIL with "ImportError: cannot import name 'from_dict'"

**Step 3: Implement from_dict**

Add to `stac_manager/utils/serialization.py`:

```python
def from_dict(
    d: dict, 
    stac_type: str | None = None
) -> pystac.STACObject:
    """
    Create PySTAC object from dict with auto-detection.
    
    Args:
        d: STAC dict
        stac_type: Optional type hint ('Item', 'Collection', 'Catalog')
        
    Returns:
        PySTAC object
    """
    if stac_type == 'Item':
        return pystac.Item.from_dict(d)
    elif stac_type == 'Collection':
        return pystac.Collection.from_dict(d)
    elif stac_type == 'Catalog':
        return pystac.Catalog.from_dict(d)
    else:
        # Auto-detect
        return pystac.read_dict(d)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/utils/test_serialization.py::test_from_dict_with_item -v`  
Expected: PASS

**Step 5: Run all serialization tests**

Run: `pytest tests/unit/utils/test_serialization.py -v`  
Expected: All PASS

**Step 6: Commit**

```bash
git add tests/unit/utils/test_serialization.py stac_manager/utils/serialization.py
git commit -m "feat(utils): add from_dict with auto-detection"
```

---

## Phase 3: Field Operations Module (`utils/field_ops.py`)

### Task 5: Field Ops - set_nested_field Basic

**Files:**
- Create: `tests/unit/utils/test_field_ops.py`
- Create: `stac_manager/utils/field_ops.py`

**Step 1: Write failing test for simple nested field**

Create `tests/unit/utils/test_field_ops.py`:

```python
import pytest
from stac_manager.utils.field_ops import set_nested_field
from tests.fixtures.stac_items import VALID_ITEM


def test_set_nested_field_simple():
    """set_nested_field sets top-level field."""
    item = VALID_ITEM.copy()
    set_nested_field(item, "id", "new-id")
    
    assert item["id"] == "new-id"


def test_set_nested_field_two_levels():
    """set_nested_field creates and sets nested field."""
    item = VALID_ITEM.copy()
    set_nested_field(item, "properties.platform", "Landsat-8")
    
    assert item["properties"]["platform"] == "Landsat-8"
    assert item["properties"]["datetime"] == "2024-01-01T00:00:00Z"  # Unchanged
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/utils/test_field_ops.py::test_set_nested_field_simple -v`  
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `stac_manager/utils/field_ops.py`:

```python
"""Field manipulation utilities for STAC items."""
from typing import Any


def set_nested_field(item: dict, path: str, value: Any) -> None:
    """
    Set nested field using dot notation.
    Creates intermediate dicts as needed.
    
    Args:
        item: STAC item dict (modified in-place)
        path: Dot-separated path (e.g., "properties.eo:cloud_cover")
        value: Value to set
    """
    keys = path.split('.')
    current = item
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/utils/test_field_ops.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add tests/unit/utils/test_field_ops.py stac_manager/utils/field_ops.py
git commit -m "feat(utils): add set_nested_field with dot notation"
```

---

### Task 6: Field Ops - get_nested_field

**Files:**
- Modify: `tests/unit/utils/test_field_ops.py`
- Modify: `stac_manager/utils/field_ops.py`

**Step 1: Write failing test for get_nested_field**

Add to `tests/unit/utils/test_field_ops.py`:

```python
from stac_manager.utils.field_ops import get_nested_field


def test_get_nested_field_exists():
    """get_nested_field retrieves existing nested value."""
    result = get_nested_field(VALID_ITEM, "properties.datetime")
    assert result == "2024-01-01T00:00:00Z"


def test_get_nested_field_missing_with_default():
    """get_nested_field returns default when path missing."""
    result = get_nested_field(VALID_ITEM, "properties.missing", default="N/A")
    assert result == "N/A"


def test_get_nested_field_missing_no_default():
    """get_nested_field returns None when path missing and no default."""
    result = get_nested_field(VALID_ITEM, "properties.missing")
    assert result is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/utils/test_field_ops.py::test_get_nested_field_exists -v`  
Expected: FAIL with "ImportError: cannot import name 'get_nested_field'"

**Step 3: Implement get_nested_field**

Add to `stac_manager/utils/field_ops.py`:

```python
def get_nested_field(item: dict, path: str, default: Any = None) -> Any:
    """
    Get nested field value using dot notation.
    
    Args:
        item: STAC item dict
        path: Dot-separated path
        default: Default value if path doesn't exist
        
    Returns:
        Field value or default
    """
    keys = path.split('.')
    current = item
    
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    
    return current
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/utils/test_field_ops.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add tests/unit/utils/test_field_ops.py stac_manager/utils/field_ops.py
git commit -m "feat(utils): add get_nested_field with default support"
```

---

### Task 7: Field Ops - deep_merge Strategy

**Files:**
- Modify: `tests/unit/utils/test_field_ops.py`
- Modify: `stac_manager/utils/field_ops.py`

**Step 1: Write failing test for deep_merge**

Add to `tests/unit/utils/test_field_ops.py`:

```python
from stac_manager.utils.field_ops import deep_merge


def test_deep_merge_overwrite_strategy():
    """deep_merge with overwrite strategy replaces values."""
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    overlay = {"b": {"c": 99, "e": 4}, "f": 5}
    
    result = deep_merge(base, overlay, strategy='overwrite')
    
    assert result["a"] == 1  # Unchanged
    assert result["b"]["c"] == 99  # Overwritten
    assert result["b"]["d"] == 3  # Unchanged
    assert result["b"]["e"] == 4  # Added
    assert result["f"] == 5  # Added


def test_deep_merge_keep_existing_strategy():
    """deep_merge with keep_existing preserves base values."""
    base = {"a": 1, "b": {"c": 2}}
    overlay = {"a": 99, "b": {"c": 99, "d": 4}}
    
    result = deep_merge(base, overlay, strategy='keep_existing')
    
    assert result["a"] == 1  # Kept (not overwritten)
    assert result["b"]["c"] == 2  # Kept
    assert result["b"]["d"] == 4  # Added (new key)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/utils/test_field_ops.py::test_deep_merge_overwrite_strategy -v`  
Expected: FAIL with "ImportError: cannot import name 'deep_merge'"

**Step 3: Implement deep_merge**

Add to `stac_manager/utils/field_ops.py`:

```python
from typing import Literal


def deep_merge(
    base: dict,
    overlay: dict,
    strategy: Literal['keep_existing', 'overwrite'] = 'overwrite'
) -> dict:
    """
    Recursively merge two dictionaries.
    
    Args:
        base: Base dictionary (modified in-place)
        overlay: Dictionary to merge into base
        strategy: Merge strategy ('overwrite' or 'keep_existing')
        
    Returns:
        Merged dictionary (same object as base)
    """
    for key, value in overlay.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            # Both are dicts - recurse
            deep_merge(base[key], value, strategy)
        elif key not in base:
            # New key - always add
            base[key] = value
        elif strategy == 'overwrite':
            # Key exists, overwrite
            base[key] = value
        # else: keep_existing - don't modify base[key]
    
    return base
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/utils/test_field_ops.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add tests/unit/utils/test_field_ops.py stac_manager/utils/field_ops.py
git commit -m "feat(utils): add deep_merge with strategy support"
```

---

### Task 8: Field Ops - JMESPath Integration

**Files:**
- Modify: `tests/unit/utils/test_field_ops.py`
- Modify: `stac_manager/utils/field_ops.py`

**Step 1: Write failing test for apply_jmespath**

Add to `tests/unit/utils/test_field_ops.py`:

```python
from stac_manager.utils.field_ops import apply_jmespath
from tests.fixtures.stac_items import NESTED_ITEM


def test_apply_jmespath_simple_path():
    """apply_jmespath extracts value with simple path."""
    result = apply_jmespath(NESTED_ITEM, "id")
    assert result == "nested-001"


def test_apply_jmespath_nested_path():
    """apply_jmespath extracts nested value."""
    result = apply_jmespath(NESTED_ITEM, "properties.\"eo:cloud_cover\"")
    assert result == 15.5


def test_apply_jmespath_array_filter():
    """apply_jmespath filters array."""
    result = apply_jmespath(NESTED_ITEM, "properties.instruments[0]")
    assert result == "OLI"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/utils/test_field_ops.py::test_apply_jmespath_simple_path -v`  
Expected: FAIL with "ImportError: cannot import name 'apply_jmespath'"

**Step 3: Implement apply_jmespath**

Add to `stac_manager/utils/field_ops.py`:

```python
import jmespath
from stac_manager.exceptions import DataProcessingError


def apply_jmespath(item: dict, query: str) -> Any:
    """
    Apply JMESPath query to item.
    
    Args:
        item: STAC item dict
        query: JMESPath query string
        
    Returns:
        Query result
        
    Raises:
        DataProcessingError: If query is invalid
    """
    try:
        return jmespath.search(query, item)
    except Exception as e:
        raise DataProcessingError(f"JMESPath query failed: {e}")
```

**Step 4: Create exceptions module**

Create `stac_manager/exceptions.py`:

```python
"""Exception hierarchy for STAC Manager."""


class StacManagerError(Exception):
    """Base exception for all STAC Manager errors."""
    pass


class ConfigurationError(StacManagerError):
    """Configuration validation failed."""
    pass


class DataProcessingError(StacManagerError):
    """Non-critical data error (item-level)."""
    pass
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/unit/utils/test_field_ops.py -v`  
Expected: All PASS

**Step 6: Commit**

```bash
git add tests/unit/utils/test_field_ops.py stac_manager/utils/field_ops.py stac_manager/exceptions.py
git commit -m "feat(utils): add apply_jmespath for field extraction"
```

---

## Phase 4: Geometry Module (`utils/geometry.py`)

### Task 9: Geometry - ensure_bbox Basic

**Files:**
- Create: `tests/unit/utils/test_geometry.py`
- Create: `stac_manager/utils/geometry.py`

**Step 1: Write failing test for ensure_bbox with Point**

Create `tests/unit/utils/test_geometry.py`:

```python
import pytest
from stac_manager.utils.geometry import ensure_bbox


def test_ensure_bbox_with_point():
    """ensure_bbox calculates bbox from Point geometry."""
    geometry = {"type": "Point", "coordinates": [1.0, 2.0]}
    result = ensure_bbox(geometry)
    
    assert result == [1.0, 2.0, 1.0, 2.0]


def test_ensure_bbox_with_none():
    """ensure_bbox returns None for None geometry."""
    result = ensure_bbox(None)
    assert result is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/utils/test_geometry.py::test_ensure_bbox_with_point -v`  
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Implement ensure_bbox (basic)**

Create `stac_manager/utils/geometry.py`:

```python
"""Geometry utilities for STAC items."""
from typing import Optional
from shapely.geometry import shape


def ensure_bbox(geometry: Optional[dict]) -> Optional[list[float]]:
    """
    Calculate bounding box from GeoJSON geometry.
    
    Args:
        geometry: GeoJSON geometry dict or None
        
    Returns:
        Bounding box [minx, miny, maxx, maxy] or None
    """
    if geometry is None:
        return None
    
    geom = shape(geometry)
    return list(geom.bounds)  # (minx, miny, maxx, maxy)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/utils/test_geometry.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add tests/unit/utils/test_geometry.py stac_manager/utils/geometry.py
git commit -m "feat(utils): add ensure_bbox for geometry types"
```

---

### Task 10: Geometry - ensure_bbox Polygon Support

**Files:**
- Modify: `tests/unit/utils/test_geometry.py`

**Step 1: Write failing test for Polygon bbox**

Add to `tests/unit/utils/test_geometry.py`:

```python
from tests.fixtures.stac_items import VALID_POLYGON, MULTI_POLYGON


def test_ensure_bbox_with_polygon():
    """ensure_bbox calculates bbox from Polygon."""
    result = ensure_bbox(VALID_POLYGON)
    
    assert result == [0.0, 0.0, 1.0, 1.0]


def test_ensure_bbox_with_multipolygon():
    """ensure_bbox calculates bbox from MultiPolygon."""
    result = ensure_bbox(MULTI_POLYGON)
    
    assert result == [0.0, 0.0, 3.0, 3.0]  # Union of both polygons
```

**Step 2: Run test to verify it passes (implementation already generic)**

Run: `pytest tests/unit/utils/test_geometry.py -v`  
Expected: All PASS (Shapely handles all geometry types)

**Step 3: Commit**

```bash
git add tests/unit/utils/test_geometry.py
git commit -m "test(utils): add polygon/multipolygon bbox tests"
```

---

### Task 11: Geometry - validate_and_repair_geometry

**Files:**
- Modify: `tests/unit/utils/test_geometry.py`
- Modify: `stac_manager/utils/geometry.py`

**Step 1: Write failing test for geometry validation**

Add to `tests/unit/utils/test_geometry.py`:

```python
from stac_manager.utils.geometry import validate_and_repair_geometry
from tests.fixtures.stac_items import INVALID_GEOMETRY, VALID_POLYGON


def test_validate_and_repair_valid_geometry():
    """validate_and_repair_geometry passes valid geometry."""
    result, warnings = validate_and_repair_geometry(VALID_POLYGON)
    
    assert result == VALID_POLYGON
    assert warnings == []


def test_validate_and_repair_invalid_geometry():
    """validate_and_repair_geometry attempts repair on invalid geometry."""
    result, warnings = validate_and_repair_geometry(INVALID_GEOMETRY)
    
    # May return repaired geometry or None (unrepairable)
    assert isinstance(warnings, list)
    assert len(warnings) > 0  # Should have warnings
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/utils/test_geometry.py::test_validate_and_repair_valid_geometry -v`  
Expected: FAIL with "ImportError: cannot import name 'validate_and_repair_geometry'"

**Step 3: Implement validate_and_repair_geometry**

Add to `stac_manager/utils/geometry.py`:

```python
from shapely import make_valid, is_valid


def validate_and_repair_geometry(geometry: dict) -> tuple[Optional[dict], list[str]]:
    """
    Validate and attempt to repair GeoJSON geometry.
    
    Args:
        geometry: GeoJSON geometry dict
        
    Returns:
        Tuple of (repaired_geometry, warnings)
        - repaired_geometry: Valid geometry or None if unrepairable
        - warnings: List of issues found/fixed
    """
    warnings = []
    geom = shape(geometry)
    
    if is_valid(geom):
        return geometry, warnings
    
    warnings.append(f"Invalid geometry detected: {explain_validity(geom)}")
    
    try:
        # Attempt repair
        repaired = make_valid(geom)
        if is_valid(repaired):
            warnings.append("Geometry repaired using make_valid")
            return repaired.__geo_interface__, warnings
    except Exception as e:
        warnings.append(f"Repair failed: {e}")
    
    return None, warnings


# Import explainvalidity helper
from shapely.validation import explain_validity
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/utils/test_geometry.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add tests/unit/utils/test_geometry.py stac_manager/utils/geometry.py
git commit -m "feat(utils): add validate_and_repair_geometry"
```

---

## Phase 5: Streaming Module (`utils/streaming.py`)

### Task 12: Streaming - async_batch

**Files:**
- Create: `tests/unit/utils/test_streaming.py`
- Create: `stac_manager/utils/streaming.py`

**Step 1: Write failing test for async_batch**

Create `tests/unit/utils/test_streaming.py`:

```python
import pytest
from stac_manager.utils.streaming import async_batch


async def async_range(n):
    """Helper: async generator for testing."""
    for i in range(n):
        yield i


@pytest.mark.asyncio
async def test_async_batch_full_batches():
    """async_batch yields full batches."""
    batches = []
    async for batch in async_batch(async_range(10), batch_size=3):
        batches.append(batch)
    
    assert len(batches) == 4  # [0,1,2], [3,4,5], [6,7,8], [9]
    assert batches[0] == [0, 1, 2]
    assert batches[1] == [3, 4, 5]
    assert batches[2] == [6, 7, 8]
    assert batches[3] == [9]  # Partial batch


@pytest.mark.asyncio
async def test_async_batch_empty_stream():
    """async_batch handles empty stream."""
    batches = []
    async for batch in async_batch(async_range(0), batch_size=5):
        batches.append(batch)
    
    assert batches == []
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/utils/test_streaming.py::test_async_batch_full_batches -v`  
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Implement async_batch**

Create `stac_manager/utils/streaming.py`:

```python
"""Async streaming utilities."""
from typing import AsyncIterator, TypeVar

T = TypeVar('T')


async def async_batch(
    iterator: AsyncIterator[T], 
    batch_size: int
) -> AsyncIterator[list[T]]:
    """
    Batch items from async iterator.
    
    Args:
        iterator: Async iterator
        batch_size: Maximum batch size
        
    Yields:
        Batches of items (last batch may be smaller)
    """
    batch = []
    async for item in iterator:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    
    # Yield remaining items
    if batch:
        yield batch
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/utils/test_streaming.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add tests/unit/utils/test_streaming.py stac_manager/utils/streaming.py
git commit -m "feat(utils): add async_batch for streaming"
```

---

### Task 13: Streaming - async_filter

**Files:**
- Modify: `tests/unit/utils/test_streaming.py`
- Modify: `stac_manager/utils/streaming.py`

**Step 1: Write failing test for async_filter**

Add to `tests/unit/utils/test_streaming.py`:

```python
from stac_manager.utils.streaming import async_filter


@pytest.mark.asyncio
async def test_async_filter():
    """async_filter filters items based on predicate."""
    def is_even(x):
        return x % 2 == 0
    
    results = []
    async for item in async_filter(async_range(10), is_even):
        results.append(item)
    
    assert results == [0, 2, 4, 6, 8]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/utils/test_streaming.py::test_async_filter -v`  
Expected: FAIL with "ImportError: cannot import name 'async_filter'"

**Step 3: Implement async_filter**

Add to `stac_manager/utils/streaming.py`:

```python
from typing import Callable


async def async_filter(
    iterator: AsyncIterator[T],
    predicate: Callable[[T], bool]
) -> AsyncIterator[T]:
    """
    Filter async iterator based on predicate.
    
    Args:
        iterator: Async iterator
        predicate: Filter function (returns True to keep)
        
    Yields:
        Items that pass predicate
    """
    async for item in iterator:
        if predicate(item):
            yield item
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/utils/test_streaming.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add tests/unit/utils/test_streaming.py stac_manager/utils/streaming.py
git commit -m "feat(utils): add async_filter for streaming"
```

---

## Phase 6: Validation Module (`utils/validation.py`)

### Task 14: Validation - hydrate_item

**Files:**
- Create: `tests/unit/utils/test_validation.py`
- Create: `stac_manager/utils/validation.py`

**Step 1: Write failing test for hydrate_item**

Create `tests/unit/utils/test_validation.py`:

```python
import pytest
from stac_manager.utils.validation import hydrate_item
from tests.fixtures.stac_items import PARTIAL_ITEM


def test_hydrate_item_with_defaults():
    """hydrate_item merges partial item with defaults."""
    defaults = {
        "type": "Feature",
        "geometry": None,
        "bbox": None,
        "properties": {"datetime": None},
        "assets": {},
        "links": []
    }
    
    result = hydrate_item(PARTIAL_ITEM, defaults=defaults)
    
    assert result["id"] == "partial-001"  # From partial
    assert result["type"] == "Feature"  # From defaults
    assert result["properties"]["datetime"] is None


def test_hydrate_item_no_defaults():
    """hydrate_item returns partial unchanged when no defaults."""
    result = hydrate_item(PARTIAL_ITEM)
    assert result == PARTIAL_ITEM
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/utils/test_validation.py::test_hydrate_item_with_defaults -v`  
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Implement hydrate_item**

Create `stac_manager/utils/validation.py`:

```python
"""STAC validation and hydration utilities."""
from typing import Optional
from stac_manager.utils.field_ops import deep_merge


def hydrate_item(partial: dict, defaults: Optional[dict] = None) -> dict:
    """
    Merge partial STAC item with defaults.
    
    Args:
        partial: Partial STAC item dict
        defaults: Default values to apply
        
    Returns:
        Hydrated item (new dict)
    """
    if defaults is None:
        return partial.copy()
    
    # Defaults are base, partial overrides
    result = defaults.copy()
    return deep_merge(result, partial, strategy='overwrite')
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/utils/test_validation.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add tests/unit/utils/test_validation.py stac_manager/utils/validation.py
git commit -m "feat(utils): add hydrate_item for partial items"
```

---

## Phase 7: Context Integration & Error Handling

### Task 15: Context-Aware Error Handling

**Files:**
- Modify: `tests/unit/utils/test_field_ops.py`
- Modify: `stac_manager/utils/field_ops.py`
- Create: `stac_manager/context.py`

**Step 1: Write failing test for context-aware error handling**

Add to `tests/unit/utils/test_field_ops.py`:

```python
from unittest.mock import Mock
from stac_manager.context import WorkflowContext


def test_set_nested_field_with_context_on_error():
    """set_nested_field logs error to context on failure."""
    mock_context = Mock(spec=WorkflowContext)
    mock_context.logger = Mock()
    mock_context.failure_collector = Mock()
    mock_context.data = {}
    
    item = {"id": "test"}
    # Attempt to set nested field on non-dict (will cause TypeError)
    item["properties"] = "not-a-dict"
    
    success = set_nested_field(
        item, 
        "properties.nested", 
        "value",
        context=mock_context
    )
    
    assert success is False
    mock_context.logger.warning.assert_called_once()
    mock_context.failure_collector.add.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/utils/test_field_ops.py::test_set_nested_field_with_context_on_error -v`  
Expected: FAIL (set_nested_field doesn't return bool or accept context)

**Step 3: Create WorkflowContext stub**

Create `stac_manager/context.py`:

```python
"""Workflow context and shared state."""
from dataclasses import dataclass
from typing import Any
import logging


@dataclass
class WorkflowContext:
    """Shared state for pipeline execution."""
    workflow_id: str
    config: Any
    logger: logging.Logger
    failure_collector: Any
    checkpoints: Any
    data: dict[str, Any]
```

**Step 4: Update set_nested_field signature**

Modify `stac_manager/utils/field_ops.py`:

```python
from typing import Optional
from stac_manager.context import WorkflowContext


def set_nested_field(
    item: dict, 
    path: str, 
    value: Any,
    *,
    context: Optional[WorkflowContext] = None
) -> bool:
    """
    Set nested field using dot notation.
    
    Args:
        item: STAC item dict (modified in-place)
        path: Dot-separated path
        value: Value to set
        context: Optional workflow context for error handling
        
    Returns:
        True if successful, False if failed
    """
    try:
        keys = path.split('.')
        current = item
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        return True
    except Exception as e:
        if context:
            context.logger.warning(f"Failed to set field '{path}': {e}")
            context.failure_collector.add(
                item_id=item.get('id', 'unknown'),
                error=e,
                step_id=context.data.get('current_step', 'unknown')
            )
            return False
        else:
            raise
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/unit/utils/test_field_ops.py -v`  
Expected: All PASS

**Step 6: Commit**

```bash
git add tests/unit/utils/test_field_ops.py stac_manager/utils/field_ops.py stac_manager/context.py
git commit -m "feat(utils): add context-aware error handling to set_nested_field"
```

---

## Phase 8: Integration & Coverage

### Task 16: Run Full Test Suite

**Step 1: Run all utility tests**

Run: `pytest tests/unit/utils/ -v --cov=stac_manager/utils --cov-report=term-missing`  
Expected: All PASS, ≥90% coverage

**Step 2: If coverage < 90%, identify gaps**

Review coverage report, add tests for uncovered branches.

**Step 3: Commit any additional tests**

```bash
git add tests/unit/utils/
git commit -m "test(utils): add coverage for edge cases"
```

---

### Task 17: Create Integration Test

**Files:**
- Create: `tests/integration/utils/test_transformer_pipeline.py`

**Step 1: Write integration test**

Create `tests/integration/utils/test_transformer_pipeline.py`:

```python
"""Integration test: utilities working together."""
import pytest
from stac_manager.utils.field_ops import apply_jmespath, set_nested_field, deep_merge
from stac_manager.utils.geometry import ensure_bbox
from stac_manager.utils.validation import hydrate_item
from tests.fixtures.stac_items import PARTIAL_ITEM


def test_transform_pipeline_integration():
    """Test utilities working together in transform-like workflow."""
    # 1. Hydrate partial item
    defaults = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-120.5, 35.2]},
        "properties": {"platform": "Landsat-8"},
        "assets": {},
        "links": []
    }
    
    item = hydrate_item(PARTIAL_ITEM, defaults=defaults)
    
    # 2. Calculate bbox from geometry
    bbox = ensure_bbox(item["geometry"])
    set_nested_field(item, "bbox", bbox)
    
    # 3. Add metadata using deep_merge
    sidecar = {
        "properties": {
            "eo:cloud_cover": 12.5,
            "instruments": ["OLI", "TIRS"]
        }
    }
    deep_merge(item, sidecar, strategy='overwrite')
    
    # 4. Extract value with JMESPath
    cloud_cover = apply_jmespath(item, "properties.\"eo:cloud_cover\"")
    
    # Verify
    assert item["id"] == "partial-001"
    assert item["bbox"] == [-120.5, 35.2, -120.5, 35.2]
    assert cloud_cover == 12.5
    assert item["properties"]["platform"] == "Landsat-8"
```

**Step 2: Run integration test**

Run: `pytest tests/integration/utils/test_transformer_pipeline.py -v`  
Expected: PASS

**Step 3: Commit**

```bash
git add tests/integration/utils/test_transformer_pipeline.py
git commit -m "test(utils): add integration test for transform pipeline"
```

---

## Phase 9: Documentation & Verification

### Task 18: Update __init__.py Exports

**Files:**
- Modify: `stac_manager/utils/__init__.py`

**Step 1: Add public exports**

Update `stac_manager/utils/__init__.py`:

```python
"""PySTAC Toolkit - Utility layer for STAC Manager."""

# Serialization
from stac_manager.utils.serialization import (
    ensure_dict,
    from_dict,
)

# Field operations
from stac_manager.utils.field_ops import (
    set_nested_field,
    get_nested_field,
    apply_jmespath,
    deep_merge,
)

# Geometry
from stac_manager.utils.geometry import (
    ensure_bbox,
    validate_and_repair_geometry,
)

# Streaming
from stac_manager.utils.streaming import (
    async_batch,
    async_filter,
)

# Validation
from stac_manager.utils.validation import (
    hydrate_item,
)

__all__ = [
    # Serialization
    "ensure_dict",
    "from_dict",
    # Field ops
    "set_nested_field",
    "get_nested_field",
    "apply_jmespath",
    "deep_merge",
    # Geometry
    "ensure_bbox",
    "validate_and_repair_geometry",
    # Streaming
    "async_batch",
    "async_filter",
    # Validation
    "hydrate_item",
]
```

**Step 2: Test imports**

Run: `python -c "from stac_manager.utils import ensure_dict, set_nested_field; print('OK')"`  
Expected: "OK"

**Step 3: Commit**

```bash
git add stac_manager/utils/__init__.py
git commit -m "feat(utils): add public API exports"
```

---

## Verification Plan

### Automated Tests

**Run full test suite:**
```bash
pytest tests/unit/utils/ tests/integration/utils/ -v --cov=stac_manager/utils --cov-report=html
```

**Success criteria:**
- All tests PASS
- Coverage ≥ 90%
- No warnings in test output
- Coverage report: `open htmlcov/index.html`

### Type Checking

**Run mypy:**
```bash
mypy stac_manager/utils/
```

**Success criteria:**
- No type errors

### Import Verification

**Test external usage pattern:**
```bash
python -c "
from stac_manager.utils import ensure_bbox, set_nested_field, deep_merge
item = {'id': 'test', 'geometry': {'type': 'Point', 'coordinates': [0, 0]}}
bbox = ensure_bbox(item['geometry'])
set_nested_field(item, 'bbox', bbox)
print(item)
"
```

**Expected output:**
```
{'id': 'test', 'geometry': {'type': 'Point', 'coordinates': [0, 0]}, 'bbox': [0.0, 0.0, 0.0, 0.0]}
```

---

## Success Criteria

- [x] All 5 utility modules implemented (`serialization`, `field_ops`, `geometry`, `streaming`, `validation`)
- [x] ≥90% test coverage
- [x] Pristine test output (no warnings)
- [x] All tests use real STAC data (no mocked domain data)
- [x] Three-tier error handling implemented (Fail Fast, Step Out, Graceful Degradation)
- [x] Context-aware functions accept optional `WorkflowContext`
- [x] Type hints enable IDE autocomplete
- [x] Public API documented via `__all__`
