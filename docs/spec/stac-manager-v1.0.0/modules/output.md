# Output Module
## STAC Manager v1.0

**Role**: `Bundler` (Sink)

---

## 1. Purpose
Materializes STAC metadata to storage (Disk, S3, etc.) in a structured format.
The primary output format is a "Static STAC" directory structure, consisting of a collection definition and individual, self-contained item files.

## 2. Architecture
- **Writers**:
    - **JSON (Default)**: Writes individual item files (`item_id.json`) and a `collection.json`.
    - **Parquet (Optional)**: writes a single `items.parquet` file at the root or configured path for bulk analytics using `stac-geoparquet`.
- **Layout**: 
    - **Exploded (Standard)**: `/{base_dir}/{collection_id}/items/{item_id}.json` (or just `/{collection_id}/items/{item_id}.json` depending on configuration).
    - **Collection File**: Always generated as `/{base_dir}/{collection_id}/collection.json`.
- **Atomicity**: MUST use the Atomic Output Pattern (write to temp, then rename/move) where possible to prevent partial file corruption.

## 3. Configuration Schema

```python
from pydantic import BaseModel
from typing import Literal, Optional, TypedDict

class OutputConfig(BaseModel):
    base_dir: str
    """
    Root directory for output.
    Example: "./data" or "s3://my-bucket/stac"
    """
    
    format: Literal['json', 'parquet'] = 'json'
    """
    Output format.
    - 'json': Individual valid JSON files (Static STAC).
    - 'parquet': Single GeoParquet file (Bulk Analytics).
    """

    BASE_URL: Optional[str] = None
    """
    Optional base URL for constructing self links.
    """

class OutputResult(TypedDict):
    """
    Result returned by OutputModule.execute().
    
    Attributes:
        files_written: List of absolute file paths created.
    """
    files_written: list[str]
```

### 3.1 Example Usage (YAML)

**Standard Static STAC Output:**
```yaml
- id: writer
  module: OutputModule
  config:
    base_dir: "./stac-output"
    format: "json"
```

**Analytics Output:**
```yaml
- id: writer_analytics
  module: OutputModule
  config:
    base_dir: "s3://data-lake/stac"
    format: "parquet"
```

## 4. I/O Contract

**Input (Workflow Context)**:
- `config` (Module Configuration):
  - `base_dir`, `format`, `BASE_URL`
- `context.data` (injected by Matrix Strategy):
  - Matrix Variables: Available for string interpolation in config.
- Items from previous step (Stream).
- `collection` object (from `WorkflowContext` metadata if available, to write `collection.json`).

**Protocol Methods** (Bundler):

```python
def bundle(self, item: dict, context: WorkflowContext) -> None:
    """
    Writes the item to the configured destination.
    
    Logic:
    1. If `BASE_URL` is configured:
       - Update item links ('self', 'root', 'parent', 'collection') to fully qualified URLs.
    
    2. If format == 'json':
       - Resolve output path: `base_dir / collection_id / items / filename_template`.
       - Write content atomically (write to temp -> rename).
       - Record file path in stats.
       
    3. If format == 'parquet':
       - Buffer item in memory (or write to temporary Arrow stream).
       - Do NOT write individual files.
    """
    ...

def finalize(self, context: WorkflowContext) -> OutputResult:
    """
    Finalizes the output process.
    
    Logic:
    1. If format == 'parquet':
       - Flush buffered items to `items.parquet`.
       - Record file path.
       
    2. If a 'collection' definition exists in context:
       - Write `collection.json` to `base_dir / collection_id /`.
       - Record file path.
       
    3. Return report of all files written.
    """
    ...
```

## 5. Directory Structure Example

For a collection `sentinel-2-l2a`:

```text
/stac-output/
└── sentinel-2-l2a/
    ├── collection.parquet # If format='parquet'
    ├── collection.json
    └── items/
        ├── S2A_TL_..._L2A.json
        ├── S2B_TL_..._L2A.json
        └── ...
```

## 6. Error Handling
- **IOError**: Fail the individual item (if recoverable) or the step (if disk full).
- **Missing Collection ID**: Items must have a `collection` field to determine the directory structure. If missing, log error and skip or put in `orphan/` directory.
