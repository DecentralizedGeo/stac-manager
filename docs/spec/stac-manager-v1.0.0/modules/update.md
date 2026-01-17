# Update Module
## STAC Manager v1.0

**Role**: `Modifier` (Processor)

---

## 1. Purpose
Modifies existing STAC metadata. Used for maintenance, patching, or enriching existing catalogs without full regeneration.

## 2. Architecture
- **Patching**: Applies updates to specific fields using dot-notation paths (e.g. `properties.eo:cloud_cover`).
- **Timestamping**: Automatically updates the `updated` timestamp if configured.

## 3. Configuration Schema

```python
from pydantic import BaseModel, Field
from typing import Dict, Any, Literal

class UpdateConfig(BaseModel):
    updates: Dict[str, Any] 
    """
    Dot-notation paths e.g. "properties.title": "New".
    Note: List values will REPLACE the target list completely; no merging of lists.
    """
    mode: Literal['merge', 'replace'] = 'merge'
```

### 3.1 Example Usage (YAML)

```yaml
- id: update
  module: UpdateModule
  config:
    mode: merge
    updates:
      "properties.title": "Updated Dataset Title"
      "assets.thumbnail.href": "https://cdn.example.com/new-thumb.png"
```

## 4. I/O Contract

**Input (Workflow Context)**:
- Items from previous step or source file.

**Output (Python)**:
```python
def modify(self, item: dict, context: WorkflowContext) -> dict:
    """
    Applies patches to the item dictionary and returns it.
    """
```

## 5. Error Handling
- **Path Not Found**: If updating a nested field that doesn't exist, create it (if `merge`) or fail (configurable).
- **Type Mismatch**: Warn if replacing a dict with a string etc.

> [!NOTE]
> **Stream State Dependency**: Updates apply to the item *as it exists at this point in the pipeline*.
> If updating extension fields that haven't been applied yet, the update will fail.
> Ensure proper step ordering via `depends_on` to apply extensions before updating their fields.
