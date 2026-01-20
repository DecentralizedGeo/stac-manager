# Static Source Module
## STAC Manager v1.0

**Role**: `Fetcher` (Source)

---

## 1. Purpose
The Static Source Module acts as a **Manual Input Source**, yielding pre-defined STAC Items (or generic dictionaries) from configuration directly into the pipeline.

It is primarily used for:
1.  **Testing/Dev**: Injecting "mock" data without requiring an external API or file.
2.  **Scaffolding**: Providing "seed" items (e.g., bare IDs) to be fleshed out by the `ScaffoldModule`.

## 2. Architecture
- **Role**: `Fetcher` (Source).
- **Mechanism**: Iterates over a list of items defined in the configuration.
- **Async Strategy**: **Simple Yield**.
  - No threading or complex async logic required.
  - **Logic (Pseudocode)**:
    ```python
    async def fetch(self, context) -> AsyncIterator[dict]:
        for item in self.config.items:
            # Optional: Simulate network delay if needed
            yield item
    ```

## 3. Configuration Schema

```python
from pydantic import BaseModel
from typing import List, Dict, Any

class StaticSourceConfig(BaseModel):
    items: List[Dict[str, Any]]
    """
    List of item dictionaries to yield. 
    Can be full STAC Items, partial dicts, or "seed" objects.
    """
```

### 3.1 Example Usage (YAML)

```yaml
- id: manual_source
  module: StaticSourceModule
  config:
    items:
      - id: "item-001"
        type: "Feature"
        properties:
           datetime: "2023-01-01T00:00:00Z"
      - id: "item-002"
        # ...
```

## 4. I/O Contract

**Input (Workflow Context)**:
- None (First step trigger).

**Side Effects (Workflow Context)**:
- None.

**Output (Python)**:
```python
AsyncIterator[dict] 
# Yields the items exactly as defined in config.
```

## 5. Error Handling
- **Config Error**: pydantic validation ensures `items` is a list.
- **Runtime**: None expected as it is purely static data.
