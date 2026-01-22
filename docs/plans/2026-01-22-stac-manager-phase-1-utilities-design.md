# STAC Manager Utilities Design
**Date**: 2026-01-22  
**Status**: Approved  
**Related**: [Research Findings](../../../../../.gemini/antigravity/brain/b37745a6-e746-44a5-a76f-65581571d971/research-findings.md)

---

## 1. Purpose & Scope

> **Context**: This document covers **Phase 1: Utilities Foundation** of the STAC Manager implementation.  
> See [Implementation Roadmap](./2026-01-22-stac-manager-roadmap.md) for the complete phased strategy.

**STAC Manager** is a standalone Python library for STAC pipeline orchestration. This design covers the foundational **utilities layer** (`stac_manager/utils/`) that will be used by STAC Manager's pipeline modules (IngestModule, TransformModule, etc.) when implemented in Phase 2.

The utilities serve dual purposes:

### Internal Use (STAC Manager Modules)
- Power modules like `IngestModule`, `TransformModule`, `ValidateModule`
- Tightly integrated with `WorkflowContext`, `FailureCollector`
- Optimized for streaming `AsyncIterator[dict]` pattern

### External Use (Custom Scripts)
- General-purpose PySTAC helpers for users bypassing full orchestration
- Standalone utilities for field manipulation, validation, geometry operations
- Decoupled from mandatory STAC Manager workflows

---

## 2. Architecture: Domain-Driven Modules (Approach A)

### Module Structure

```
stac_manager/
├── utils/
│   ├── __init__.py          # Public exports
│   ├── serialization.py     # dict ↔ PySTAC conversion
│   ├── field_ops.py         # Dot notation, JMESPath, deep_merge
│   ├── geometry.py          # ensure_bbox, validate_geometry
│   ├── streaming.py         # Async iterator utilities
│   └── validation.py        # Item hydration, schema validation
```

### Module Responsibilities

#### `utils/serialization.py`
```python
def to_dict(obj: pystac.STACObject) -> dict
def from_dict(d: dict, stac_type: Literal['Item', 'Collection', 'Catalog'] | None = None) -> pystac.STACObject
def ensure_dict(obj: dict | pystac.STACObject) -> dict
```

#### `utils/field_ops.py`
```python
def set_nested_field(item: dict, path: str, value: Any) -> None
def get_nested_field(item: dict, path: str, default: Any = None) -> Any
def apply_jmespath(item: dict, query: str) -> Any
def deep_merge(base: dict, overlay: dict, strategy: Literal['keep_existing', 'overwrite']) -> dict
```

#### `utils/geometry.py`
```python
def ensure_bbox(geometry: dict | None) -> list[float] | None
def validate_and_repair_geometry(geometry: dict) -> tuple[dict | None, list[str]]
```

#### `utils/streaming.py`
```python
async def async_batch(iterator: AsyncIterator[T], batch_size: int) -> AsyncIterator[list[T]]
async def async_filter(iterator: AsyncIterator[T], predicate: Callable) -> AsyncIterator[T]
```

#### `utils/validation.py`
```python
def hydrate_item(partial: dict, defaults: dict | None = None) -> dict
def validate_stac_item(item: dict, strict: bool = False) -> tuple[bool, list[str]]
```

---

## 3. Design Decisions

### 3.1 Wire Format: `dict` Only (Not Polymorphic)

**Decision**: Utilities operate exclusively on `dict`, not `dict | pystac.STACObject`.

**Rationale**:
- Matches STAC Manager's pipeline wire format (`AsyncIterator[dict]`)
- Simpler implementation and testing
- External users can call `to_dict()` themselves if needed
- YAGNI - add polymorphism only if users request it

### 3.2 Error Handling: Three-Tier Model

#### Tier 1: Fail Fast (Configuration/Startup)
```python
def validate_strategy(strategy: str) -> None:
    if strategy not in VALID_STRATEGIES:
        logger.error(f"Invalid strategy: {strategy}")
        raise ConfigurationError(f"Invalid strategy: {strategy}")
```

#### Tier 2: Step Out (Item-Level Non-Critical)
```python
def set_nested_field(
    item: dict, 
    path: str, 
    value: Any,
    *, 
    context: WorkflowContext | None = None
) -> bool:  # Returns success/failure
    try:
        _apply_nested_field(item, path, value)
        return True
    except Exception as e:
        if context:
            context.logger.warning(f"Failed to set field '{path}': {e}")
            context.failure_collector.add(
                item_id=item.get('id', 'unknown'),
                error=e,
                step_id=context.data.get('current_step', 'unknown')
            )
            return False  # Continue processing
        else:
            raise  # External usage - fail loudly
```

#### Tier 3: Graceful Degradation (Optional Features)
```python
def ensure_bbox(geometry: dict | None) -> list[float] | None:
    if geometry is None:
        return None  # Valid case
    try:
        return calculate_bbox(geometry)
    except ImportError:
        logger.warning("Shapely not installed - bbox unavailable")
        return None  # Continue without bbox
```

### 3.3 Context Integration Pattern

Utilities accept optional `context: WorkflowContext | None` via keyword-only argument:
- **If context provided**: Log to `context.logger`, collect errors in `context.failure_collector`
- **If context absent**: Raise exceptions directly (external script usage)

---

## 4. Integration Patterns

### Internal Use (STAC Manager Modules)

```python
# In TransformModule.modify()
from stac_manager.utils.field_ops import set_nested_field

def modify(self, item: dict, context: WorkflowContext) -> dict | None:
    success = set_nested_field(
        item, 
        "properties.datetime", 
        transformed_date,
        context=context
    )
    if not success:
        return None  # Drop item
    return item
```

### External Use (Custom Scripts)

```python
# User's custom script
from stac_manager.utils.geometry import ensure_bbox

items = load_json("my_items.json")
for item in items:
    if not item.get("bbox"):
        item["bbox"] = ensure_bbox(item["geometry"])
```

---

## 5. Testing Strategy

### Test Structure
```
tests/
├── unit/
│   └── utils/
│       ├── test_serialization.py
│       ├── test_field_ops.py
│       ├── test_geometry.py
│       ├── test_streaming.py
│       └── test_validation.py
└── integration/
    └── utils/
        └── test_transformer_pipeline.py
```

### Key Principles

1. **No Mocks on Domain Data**: Use real STAC items, geometries, etc.
2. **Mocks for Infrastructure**: HTTP requests, file I/O, WorkflowContext
3. **≥90% Coverage**: Including error paths for all three tiers
4. **Test Categories**:
   - Happy path (valid inputs)
   - Edge cases (null geometry, missing fields)
   - Error paths (all 3 error tiers)
   - Integration (utilities working together)

### Example Test Data

```python
# tests/fixtures/stac_items.py
VALID_ITEM = {
    "type": "Feature",
    "stac_version": "1.0.0",
    "id": "test-item-001",
    "geometry": {"type": "Point", "coordinates": [0, 0]},
    "bbox": [0, 0, 0, 0],
    "properties": {"datetime": "2024-01-01T00:00:00Z"},
    "assets": {},
    "links": []
}

PARTIAL_ITEM = {"id": "partial-001"}
INVALID_GEOMETRY = {"type": "Polygon", "coordinates": [[0, 0]]}  # Unclosed
```

---

## 6. Dependencies

### Core (STAC Manager)
```toml
[tool.poetry.dependencies]
python = "^3.12"
pystac = "^1.10.0"
pystac-client = "^0.7.0"
stac-validator = "^3.3.0"
stac-geoparquet = "^0.4.0"
jmespath = "^1.0.1"
shapely = "^2.0.0"
pydantic = "^2.0.0"
httpx = "^0.27.0"
aiofiles = "^23.0.0"
```

### Where Used
- `stac-geoparquet` → OutputModule (Parquet bundling)
- `stac-validator` → ValidateModule + `utils/validation.py`
- `jmespath` → `utils/field_ops.py` (TransformModule)
- `shapely` → `utils/geometry.py`

---

## 7. Performance Considerations

### 7.1 Lazy Evaluation
```python
# Good: Generator for memory efficiency
def batch_items(items: list[dict], batch_size: int) -> Iterator[list[dict]]:
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]
```

### 7.2 Avoid Redundant Conversions
```python
# Bad: Multiple serialization cycles
item_obj = pystac.Item.from_dict(item_dict)
modified = item_obj.to_dict()

# Good: Direct dict manipulation
modified = item_dict.copy()
set_nested_field(modified, "properties.datetime", value)
```

### 7.3 Cache Expensive Operations
```python
# In TransformModule
class TransformModule:
    def __init__(self, config):
        self._jmespath_cache = {}
    
    def _compile_jmespath(self, query: str):
        if query not in self._jmespath_cache:
            self._jmespath_cache[query] = jmespath.compile(query)
        return self._jmespath_cache[query]
```

---

## 8. Out of Scope (v1.0)

### Deferred to v2.0
- **Multiprocessing utilities**: Current architecture (asyncio) handles I/O-bound workloads efficiently. Multiprocessing adds complexity without proven need.
- **Parquet batch helpers**: Keep in OutputModule for now. Can extract later if reuse emerges.
- **Polymorphic input**: `dict | pystac.STACObject` support deferred until user demand.

---

## 9. Success Criteria

### For STAC Manager Modules
- ✅ All modules use utilities for field manipulation, validation, geometry
- ✅ No direct PySTAC object manipulation in pipeline (dict wire format)
- ✅ Consistent error handling across all modules (three-tier model)

### For External Users
- ✅ Can import utilities standalone without STAC Manager orchestration
- ✅ Clear documentation with usage examples
- ✅ Type hints enable IDE autocomplete

### Quality Metrics
- ✅ 90%+ test coverage on all utilities
- ✅ Pristine test output (no warnings)
- ✅ All edge cases handled with explicit error messages
