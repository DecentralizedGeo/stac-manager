# Utilities & Shared Components
## STAC Manager v1.0

**Related Documents**:
- [Protocols](./06-protocols.md)
- [Pipeline Management](./01-pipeline-management.md)

---

## Overview

This document defines shared utility components used across multiple modules. These are **conceptual specifications** - they describe requirements and behavior without prescribing exact implementation.

---

## 1. Query Utilities

### 1.1 Temporal Request Splitting

**Purpose**: recursively split large time ranges to avoid deep pagination and server timeouts.

**Algorithm**:
1. Query with `limit=0` to get count.
2. If count > `threshold` (e.g., 10,000):
   - Split time range in half (midpoint).
   - Recursively process both halves.
3. If count <= `threshold`:
   - Proceed with standard pagination.

**Function Signature**:
```python
async def temporal_split_search(
    client: Client,
    collection_id: str,
    time_range: Optional[tuple[datetime, datetime]] = None,
    bbox: Optional[list[float]] = None,
    limit: int = 10000
):
    """
    Generator that yields STAC items from a search, splitting by time if needed.
    Used by IngestModule to handle large result sets without timeouts.
    """
    # Implementation logic...
```

---

## 2. Geometry Utilities

### 2.1 Bbox Calculation

**Purpose**: Ensure STAC Items have valid bounding boxes

**Function Signature**:
```python
def ensure_bbox(geometry: dict | None) -> list[float] | None:
    """
    Calculate bounding box from GeoJSON geometry.
    
    Args:
        geometry: GeoJSON geometry dict or None
    
    Returns:
        Bounding box [minx, miny, maxx, maxy] or None if geometry is None
    
    Behavior:
        Must correctly handle all GeoJSON geometry types:
        - Point, MultiPoint
        - LineString, MultiLineString
        - Polygon, MultiPolygon
        - GeometryCollection
        
        Returns None if geometry parameter is None.
        For valid geometries, returns [west, south, east, north] coordinate bounds.
    """
    ...
```

**Usage**:
```python
# In SeedModule
bbox = ensure_bbox(transformed_data['geometry'])
```

### 2.2 Geometry Validation and Repair

**Purpose**: Fix common geometry issues (unclosed polygons, invalid coordinates)

**Function Signature**:
```python
def validate_and_repair_geometry(geometry: dict) -> tuple[dict | None, list[str]]:
    """
    Validate and attempt to repair GeoJSON geometry.
    
    Args:
        geometry: GeoJSON geometry dict
    
    Returns:
        Tuple of (repaired_geometry, warnings)
        - repaired_geometry: Valid geometry or None if unrepairable
        - warnings: List of issues found/fixed
    
    Implementation:
        1. Check `shapely.is_valid`.
        2. If invalid, attempt `shapely.make_valid` (GEOS >= 3.8).
        3. Fallback: `geometry.buffer(0)` check.
        4. If still invalid, return None (unrepairable).
    """
    ...
```

---

## 2.3. Deep Dictionary Merge

**Purpose**: Recursively merge two dictionaries with configurable conflict resolution.

**Function Signature**:
```python
from typing import Any, Literal

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
        strategy: Merge strategy for conflict resolution
            - 'overwrite': overlay values replace base values (default)
            - 'keep_existing': base values preserved, only add new keys from overlay
    
    Returns:
        Merged dictionary (same object as base)
        
    Behavior:
        For each key in overlay:
        - If key not in base: add the key-value pair
        - If both values are dicts: recursively merge the nested dicts
        - If both values are lists: replace base list with overlay list (no list merging)
        - Otherwise: apply the specified strategy
        
    Examples:
        >>> base = {"a": 1, "b": {"c": 2}}
        >>> overlay = {"b": {"d": 3}, "e": 4}
        >>> deep_merge(base, overlay)
        {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}
    """
    ...
```

---

## 3. State Persistence (Checkpointing)

### 3.1 Purpose
Allow long-running async workflows to resume from where they left off after a crash or interruption.

### 3.2 Detailed Specification
See [State Persistence & Recovery](./08-state-persistence.md) for the complete architecture, data schema, and API definition.

### 3.3 Shared Pattern: Atomic Output
(Moved to [08-state-persistence.md](./08-state-persistence.md#5-atomic-write-strategy))

Modules writing files MUST follow the atomic write protocols defined in the State Persistence spec.

---

## 4. Logging Utilities

### 4.1 Logger Setup

**Purpose**: Configure structured logger from workflow config, ensuring library safety and log rotation.

**Function Signature**:
```python
def setup_logger(config: dict) -> logging.Logger:
    """
    Create configured logger instance.
    
    Args:
        config: Workflow configuration with logging section
    
    Returns:
        Configured logger with console and optional file handlers
    
    Configuration:
        settings:
          logging:
            level: DEBUG | INFO | WARNING | ERROR
            file: path/to/log/file.log (optional, default: logs/stac_manager.log)
            output_format: json | text (default: text)
    
    Behavior:
        - Gets logger 'stac_manager'
        - Sets propagate=False to avoid duplicate logs when used as library
        - Always adds console handler (stdout) with simplified format
        - Adds RotatingFileHandler if 'file' configured or default
          - MaxBytes: 10MB
          - BackupCount: 5
        - Uses structured JSON format for file if output_format='json'
    """
    ...
```

### 4.2 Structured Logging Pattern

**Module Logging Convention**:
```python
# In any module
async def execute(self, context: WorkflowContext):
    context.logger.info(f"[{self.__class__.__name__}] Starting execution")
    
    # ... work ...
    
    context.logger.info(
        f"[{self.__class__.__name__}] Completed: {count} items processed"
    )
```

**Log Level Guidelines**:

| Level | Usage |
|-------|-------|
| **DEBUG** | Detailed diagnostic info (field mappings, API responses, intermediate values) |
| **INFO** | Progress updates (step start/completion, item counts, milestones) |
| **WARNING** | Non-critical errors (validation failures, skipped items, retries) |
| **ERROR** | Critical failures (module exceptions, I/O errors, config errors) |

---

## 5. Processing Summary Generator

### 5.1 Purpose
Create human-readable summary of workflow execution results

### 5.2 Function Signature

```python
def generate_processing_summary(
    result: WorkflowResult, 
    context: WorkflowContext
) -> str:
    """
    Generates a human-readable markdown summary of the workflow execution.
    
    Args:
        result: WorkflowResult dict
        context: WorkflowContext object
        
    Returns:
        Formatted summary string for console output
    
    Output Format:
        === Workflow Processing Summary ===
        Workflow: {name}
        Total Steps: {total}
        Successful Steps: {success}
        Failed Steps: {failed}
        
        === Failure Breakdown ===
        Total Failures: {count}
        
        {step_id}: {failure_count} failures
        ...
        
        Detailed failure report: {path}
    """
    ...
```

### 5.3 Usage

```python
# In CLI or StacManager
result = await orchestrator.execute()
summary = generate_processing_summary(result, context.failure_collector)
print(summary)
```

---

## 6. Configuration Validation

### 6.1 Workflow Config Validator

**Purpose**: Validate workflow YAML before execution

**Function Signature**:
```python
def validate_workflow_config(config: dict) -> list[str]:
    """
    Validate workflow configuration structure and requirements.
    
    Args:
        config: Loaded workflow configuration dictionary
    
    Returns:
        List of validation errors (empty if valid)
    
    Checks:
        - Required fields present (workflow.name, workflow.steps)
        - All step IDs are unique
        - All dependencies reference valid step IDs
        - No circular dependencies
        - Each step has required fields (id, module, config)
        - Module names are valid
    """
    ...
```

**Usage**:
```python
# Before executing workflow
errors = validate_workflow_config(config)
if errors:
    for error in errors:
        print(f"Configuration error: {error}")
    sys.exit(1)
```

---

## 7. Variable Substitution

### 7.1 Purpose
Resolve `${VAR_NAME}` and `${VAR_NAME:-default}` placeholders in configuration from environment variables and matrix context, supporting recursive substitution and automatic type inference.

### 7.2 Class Interface

```python
from typing import Any, Dict
import os

class VariableSubstitutor:
    """
    Handles recursive environment and matrix variable substitution with type inference.
    
    Supports patterns:
    - ${VAR_NAME}: Replace with value from environment or context
    - ${VAR_NAME:-default}: Replace with value, or use default if not found
    
    Priority: context_vars > env_vars
    """
    
    def __init__(self, env_vars: Dict[str, str] | None = None):
        """
        Initialize substitutor with environment variables.
        
        Args:
            env_vars: Optional environment variable override (defaults to os.environ)
        """
        self.env_vars = env_vars or dict(os.environ)
    
    def substitute(
        self, 
        value: Any, 
        context_vars: Dict[str, Any] | None = None
    ) -> Any:
        """
        Recursively substitute variables in any value type.
        
        Args:
            value: Value to process (str, dict, list, or primitive)
            context_vars: Optional context/matrix variables (take priority over env)
            
        Returns:
            Value with all variable patterns resolved
            
        Behavior:
            - Strings: Substitute patterns with type inference
              - "123" -> 123 (int)
              - "3.14" -> 3.14 (float)
              - "true"/"false" -> True/False (bool)
              - Other strings remain strings
            - Dicts: Recursively process all values
            - Lists: Recursively process all elements  
            - Primitives (int, float, bool, None): Return unchanged
            
        Raises:
            ConfigurationError: If ${VAR} has no default and VAR not found in environment or context
            
        Examples:
            >>> sub = VariableSubstitutor()
            >>> sub.substitute("${PORT}", {"PORT": "8080"})
            8080  # Note: auto-converted to int
            
            >>> sub.substitute("${URL:-https://default.com}", {})
            "https://default.com"
            
            >>> sub.substitute({"port": "${PORT}"}, {"PORT": "3000"})
            {"port": 3000}
        """
        ...
```

---

## 8. Summary

This document defines:

- **Query Utilities**: Temporal splitting for deep pagination results
- **Geometry Utilities**: Bbox calculation and validation
- **State Persistence**: Checkpointing and atomic writes
- **Logging Setup**: Structured logger configuration with rotation
- **Processing Summary**: Workflow result reporting (StacManager)
- **Config Validation**: Pre-execution checks
- **Env Var Substitution**: Secure credential handling with defaults
