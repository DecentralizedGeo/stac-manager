# Validate Module
## STAC Manager v1.0

**Role**: `Modifier` (Processor)

---

## 1. Purpose
Validates STAC Items and Collections against the core STAC specification (v1.1.0).

## 2. Architecture
- **Backing**: Uses `stac-validator` library.
- **Batching**: Capable of validating streams of items efficiently.
- **Reporting**: Generates detailed validation reports for failures.
- **Performance**: The `stac-validator` library can be heavy to initialize. The validator MUST be instantiated once in `__init__`, not per item in `modify`.

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
- `config` (Module Configuration):
  - `strict`: Validation strictness.
  - `extension_schemas`: Additional schemas to validate against.
- `context.data` (injected by Matrix Strategy):
  - Matrix Variables: Available for string interpolation in config.
- Items from previous step (Stream).

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
    # 1. Validate
    is_valid, errors = self.validator.validate(item)

    if not is_valid:
        # A. Strict Mode: Abort Workflow
        if self.config.strict:
            raise ModuleException(f"Validation failed for {item.get('id')}: {errors}")
        
        # B. Lenient Mode: Collect Error & Drop Item
        context.failure_collector.add(
            item_id=item.get('id', 'unknown'),
            step_id="validate",
            error="ValidationFailed",
            message=str(errors)
        )
        return None  # Drop from stream
    
    return item
```

- **Schema Unreachable**: Log warning. If `strict` is True, raise `ModuleException`.
