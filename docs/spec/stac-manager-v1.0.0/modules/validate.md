# Validate Module
## STAC Manager v1.0

**Role**: `Modifier` (Processor)

---

## 1. Purpose
Validates STAC Items and Collections against the core STAC specification (v1.1.0) and any registered extensions.

## 2. Architecture
- **Backing**: Uses `stac-validator` library.
- **Batching**: Capable of validating streams of items efficiently.
- **Reporting**: Generates detailed validation reports for failures.

## 3. Configuration Schema

```python
from pydantic import BaseModel, HttpUrl
from typing import List

class ValidateConfig(BaseModel):
    strict: bool = False
    """
    If True, validation errors raise `ModuleException` (aborting the workflow).
    If False, validation errors raise `DataProcessingError` (detected and collected).
    """
    extension_schemas: List[HttpUrl] = []
```

### 3.1 Example Usage (YAML)

```yaml
- id: validate
  module: ValidateModule
  config:
    strict: true
    extension_schemas:
      - "https://example.com/schemas/my-extension.json"
```

## 4. I/O Contract

**Input (Workflow Context)**:
- Items from previous step.

**Output (Python)**:
```python
def modify(self, item: dict, context: WorkflowContext) -> dict | None:
    """
    Validates item and returns it. Returns None if invalid (item is dropped).
    The behavior for invalid items depends on `strict` config.
    """
```

## 5. Error Handling
- **Invalid Item**: Item is dropped from the stream. Error details (schema path, message) are sent to `FailureCollector`.

### 5.1 Failure Collection Pseudocode
```python
if not is_valid:
    context.failure_collector.log(
        item_id=item['id'],
        step_id="validate",
        error=f"Validation failed: {errors}"
    )
    return None # Drop item
```

- **Schema Unreachable**: Log warning. If `strict` is True, fail.
