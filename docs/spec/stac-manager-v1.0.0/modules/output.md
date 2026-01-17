# Output Module
## STAC Manager v1.0

**Role**: `Bundler` (Sink)

---

## 1. Purpose
Materializes STAC metadata to storage (Disk, S3, etc.) in the desired format (JSON, Parquet).

## 2. Architecture
- **Writers**: Uses `PySTAC` for JSON and `stac-geoparquet` for Parquet.
- **Layout**: Manages directory structure (e.g. `collection/item_id/item.json`).
- **Manifest**: Generates a list of all files written for downstream processing (e.g. `pgstac` ingestion).
- **Atomicity**: MUST use the Atomic Output Pattern (see [State Persistence](../08-state-persistence.md#5-atomic-write-strategy)) to prevent data corruption during partial writes.

## 3. Configuration Schema

```python
from pydantic import BaseModel
from typing import Literal

class OutputConfig(BaseModel):
    format: Literal['json', 'parquet']
    output_path: str
    organize_by: Literal['item_id', 'flat'] = 'item_id'

class OutputResult(TypedDict):
    """
    Result returned by OutputModule.execute().
    
    Attributes:
        files_written: List of absolute file paths corresponding to the 'path' field in the manifest.
        manifest_path: Absolute path to the generated manifest.json file.
        manifest: The full dictionary content of the manifest (see Data Contracts).
    """
    files_written: list[str]
    manifest_path: str
    manifest: dict
```

### 3.1 Example Usage (YAML)

```yaml
- id: output
  module: OutputModule
  config:
    format: parquet
    output_path: "s3://my-bucket/stac-output"
    organize_by: item_id
```

## 4. I/O Contract

**Input (Workflow Context)**:
- Items from previous step (via `context.data` stream reference).

**Protocol Methods** (Bundler):

```python
def bundle(self, item: dict, context: WorkflowContext) -> None:
    """
    Add an item to the current write buffer.
    
    Behavior:
        - Accumulates items until batch_size is reached
        - Flushes buffer to disk when full (atomic write)
    """
    ...

def finalize(self, context: WorkflowContext) -> OutputResult:
    """
    Flush any remaining items and generate execution manifest.
    
    Returns:
        OutputResult containing files_written, manifest_path, and manifest dict.
        See: Data Contracts - Output Result Schema
    """
    ...
```

> [!NOTE]
> **Related Documents**: See [Protocols - Bundler](../06-protocols.md#13-bundler-sink) and [Data Contracts - Output Result](../05-data-contracts.md#6-output-result-schema).

## 5. Error Handling
- **IOError**: Log failure (disk full, permission).
- **Format Error**: If data cannot be serialized to Parquet (e.g. mixed schemas), fail batch or item.

