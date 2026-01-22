# Data & System Contracts
## STAC Manager v1.0

**Related Documents**:
- [Protocols](./06-protocols.md)
- [Pipeline Management](./01-pipeline-management.md)

---

This document defines the strict data structures and contracts used for inter-module communication, ensuring type safety and memory efficiency.

## 1. Data Exchange Standards

To support large-scale catalogs (1M+ items) and ensure module interoperability, the pipeline adheres to strict data exchange standards.

### 1.1 Wire Format

- **The Pipe**: `AsyncIterator[dict]`
- **The Item**: Python `dict` (Standardized STAC Item structure)

### 1.2 Memory Constraint (Streaming)

Pipeline execution **MUST** use Iterators/Generators to maintain a constant memory profile.

**Requirement**: Item-processing modules **MUST NOT** accumulate entire streams into `list[dict]` in-memory. They must yield results as they are processed.

### 1.3 Rationale: Why `dict`?

1.  **Performance**: Avoids redundant serialization/deserialization cycles between every step in the pipeline.
2.  **Stability**: Pass-through data (fields not used by a specific module) remains untouched and safe from library-version-specific parsing quirks.
3.  **Flexibility**: Allows non-STAC or "Dirty" metadata (from Transform modules) to flow through the same pipeline structure before being modified by downstream modules.

---

## 2. System Contracts (Exceptions & Contexts)

### 2.1 Exception Hierarchy

Stac Manager defines a strict hierarchy of exceptions for control flow.

```python
class StacManagerError(Exception):
    """Base exception for all STAC Manager errors."""
    pass

class ConfigurationError(StacManagerError):
    """
    Configuration validation failed.
    Usage: Raise at startup when config is invalid.
    Effect: Workflow aborts before execution starts.
    """
    pass

class ModuleException(StacManagerError):
    """
    Critical module error.
    Usage: Raise when module cannot continue (missing dependency, invalid state).
    Effect: Workflow step fails, orchestrator aborts (or continues to next branch).
    """
    pass

class WorkflowConfigError(StacManagerError):
    """
    Invalid workflow definition.
    Usage: Raise when workflow has structural errors (cycles, missing steps).
    Effect: Workflow aborts before execution starts.
    """
    pass

class WorkflowExecutionError(StacManagerError):
    """
    Workflow execution failed.
    Usage: Raised by orchestrator when critical step fails.
    Effect: Workflow terminates, error logged.
    """
    pass

class DataProcessingError(StacManagerError):
    """
    Non-critical data error.
    Usage: For item-level failures that should be collected.
    Effect: Caught by module/orchestrator, logged to FailureCollector.
    """
    pass

class ExtensionError(StacManagerError):
    """
    Extension apply/validate error.
    Usage: When extension cannot be applied to item.
    Effect: Depends on context (may be collected or raised).
    """
    pass
```

### 2.2 WorkflowContext

The shared state object passed to every module's `execute()` method.

```python
from dataclasses import dataclass
from typing import Any, TypedDict
import logging
# from stac_manager.config import WorkflowDefinition (Forward Ref)

@dataclass
class WorkflowContext:
    """Shared state for pipeline execution."""
    workflow_id: str                      # Unique execution identifier
    config: Any                           # Full workflow definition (WorkflowDefinition)
    logger: logging.Logger                # Structured logger instance
    failure_collector: 'FailureCollector' # Error aggregator
    checkpoints: 'CheckpointManager'      # State persistence manager
    data: dict[str, Any]                  # Inter-step ephemeral data & Matrix variables

    def fork(self, data: dict[str, Any]) -> 'WorkflowContext':
        """
        Create a child context with isolated data.
        Used for Matrix Strategy to spawn parallel, isolated pipelines.
        """
        ...
```

### 2.3 FailureCollector

Aggregates non-critical errors during workflow execution.

```python
from dataclasses import dataclass
from typing import TypedDict, Optional

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
    step_id: str          # Step where failure occurred
    item_id: str          # Item/record identifier (or "unknown")
    error_type: str       # Exception class name or error category
    message: str          # Error message
    timestamp: str        # ISO 8601 timestamp
    context: Optional[FailureContext]  # Optional additional context

class FailureCollector:
    """
    Collects non-critical failures for reporting.
    """
    def add(self, item_id: str, error: str | Exception, step_id: str = 'unknown', error_context: FailureContext | None = None) -> None:
        ...
    
    def get_all(self) -> list[FailureRecord]:
        ...
```

---

## 3. Intermediate Data Schema

The contract for `TransformModule`.

```python
from typing import TypedDict, Any

class TransformedItem(TypedDict, total=False):
    """
    Standardized dictionary output from TransformModule.
    Does not strictly require valid STAC fields yet, but MUST possess structure.
    """
    id: str                             # Required: Item identifier
    geometry: dict | None               # GeoJSON geometry or None
    bbox: list[float] | None            # Bounding box [minx, miny, maxx, maxy]
    datetime: str | None                # ISO 8601 datetime string
    properties: dict[str, Any]          # Additional properties
    assets: dict[str, dict]             # Asset definitions (key -> asset dict)
    links: list[dict] | None            # Optional link objects
```

**Usage**: See [Protocols](./06-protocols.md#31-transformeditem) for full specification.

---

## 4. Failure Report Schema

The schema of the `failures.json` file generated at workflow end.

### 4.1 Complete Schema

```json
{
  "workflow_name": "string",
  "workflow_id": "uuid-string (optional)",
  "started_at": "iso-timestamp",
  "ended_at": "iso-timestamp",
  "total_steps": 5,
  "total_failures": 12,
  "failures_by_step": {
    "ingest": 8,
    "transform": 3,
    "validate": 1
  },
  "failures": [
    {
      "step_id": "transform",
      "item_id": "item-abc-123",
      "error_type": "ValidationError",
      "message": "Missing required field 'datetime'",
      "timestamp": "2024-01-15T12:30:45Z",
      "context": {
        "source_file": "data/modis.csv",
        "line_number": 45,
        "field_name": "datetime"
      }
    }
  ]
}
```

### 4.2 Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `workflow_name` | string | Workflow name from config |
| `workflow_id` | string? | Optional UUID for workflow run |
| `started_at` | string | ISO 8601 timestamp of workflow start |
| `ended_at` | string | ISO 8601 timestamp of workflow completion |
| `total_steps` | integer | Total number of workflow steps |
| `total_failures` | integer | Total number of item-level failures |
| `failures_by_step` | dict | Failure counts grouped by step_id |
| `failures` | array | Detailed failure records |

### 4.3 Failure Record Fields

| Field | Type | Description |
|-------|------|-------------|
| `step_id` | string | Step where failure occurred |
| `item_id` | string | Item identifier (or "unknown") |
| `error_type` | string | Exception class name or category |
| `message` | string | Human-readable error description |
| `timestamp` | string | ISO 8601 timestamp of failure |
| `context` | object? | Optional additional debugging info |

### 4.4 Context Object (Optional)

The `context` field may contain step-specific debugging information:

```json
{
  "source_file": "data/input.csv",
  "line_number": 123,
  "field_name": "geometry",
  "url": "https://api.example.com/items/abc",
  "http_status": 429,
  "retry_attempt": 3
}
```

---

## 5. Query Language Standard

For all configuration fields involving field selection or mapping (e.g., `TransformModule` schemas, filtering logic):

- **Standard**: [JMESPath](https://jmespath.org/)
- **Library**: `jmespath` (Python)
- **Rationale**: Standard, robust, security-safe (no `eval`)

**Example**: Transform schema using JMESPath  

```yaml
mappings:
  - source_field: "metadata.acquisition.datetime"
    target_field: "properties.datetime"
    type: datetime
```

---

## 6. Output Result Schema

Result structure returned by `OutputModule.finalize()`:

```python
from typing import TypedDict

class OutputResult(TypedDict):
    """
    Result returned by OutputModule.finalize().
    
    Provides information about files written during output.
    """
    files_written: list[str]    # Absolute paths to written files
```

---

## 7. Workflow Result Schema

Result structure returned by `StacManager.execute()`:

```python
from typing import TypedDict, Literal

class WorkflowResult(TypedDict):
    """
    Result of a complete workflow execution.
    """
    success: bool                                              # Overall success (no critical crashes)
    status: Literal['completed', 'completed_with_failures', 'failed']
    summary: str                                               # Human-readable summary
    failure_count: int                                         # Total item-level failures
    failures_path: str | None                                  # Path to failures.json (if any)
```

---

## 8. Summary

This document defines:

1. **Streaming Requirement**: Use `AsyncIterator` not `list` for items
2. **Wire Format**: Strict `dict` usage for inter-module communication
3. **TransformedItem**: Contract for Transform module
4. **Failure Report**: Complete schema for error tracking
5. **Query Language**: JMESPath for field mapping
6. **OutputResult**: Return type for OutputModule.finalize()
7. **WorkflowResult**: Return type for StacManager.execute()

These contracts ensure type safety and enable large-scale processing.

