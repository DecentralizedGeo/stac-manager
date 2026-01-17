# Scaffold Module
## STAC Manager v1.0

**Role**: `Modifier` (Processor)

---

## 1. Purpose
Generates valid STAC v1.1.0 Items and Collections from intermediate data or templates. It ensures the "structural integrity" of the STAC objects.

## 2. Architecture
- **Factory**: Creates `pystac.Item` objects.
- **Validator**: Ensures minimal field presence (geometry, bbox, datetime).
- **Linker**: Generates relative links between Items and Collections.
- **Defaults**: Applies configured defaults for missing mandatory metadata (e.g., `license`, `extent`).
  - *Rationale*: `pystac` objects do not default required fields. Defaults ensure validity.
- **Template Generator**: Generates empty boilerplate JSON for new collections/catalogs (when `mode: template`).

### 2.1 Template Generation Logic
When `mode: template` is active, the module ignores input streams and generates files based on `template.type`:

1.  **Catalog (`type: catalog`)**:
    - Generates `catalog.json` with minimal root structure.
    - Adds `rel: self` and `rel: root` links.
2.  **Collection (`type: collection`)**:
    - Generates `collection.json` with configured `collection_id`.
    - Adds placeholder `extent` (global coverage).
    - Adds default `license` and `providers`.
3.  **Item (`type: item`)**:
    - Generates `item.json` (or sample file).
    - Includes dummy `geometry` (null or center point) and `datetime`.
    - Used for testing extensions or scaffolding new datasets.

### 2.2 Strict Schema Adherence
The module ensures compliance with the official STAC JSON Schemas:
- [Catalog Spec](https://github.com/radiantearth/stac-spec/blob/master/catalog-spec/json-schema/catalog.json)
- [Collection Spec](https://github.com/radiantearth/stac-spec/blob/master/collection-spec/json-schema/collection.json)
- [Item Spec](https://github.com/radiantearth/stac-spec/blob/master/item-spec/json-schema/item.json)

**Note**: The `defaults` configuration matches values to required schema fields that are NOT auto-populated by `pystac`.

## 3. Configuration Schema

```python
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Literal, Dict, Any, List

class Provider(BaseModel):
    name: str
    roles: List[str] # ["host", "processor", ...]
    url: Optional[HttpUrl] = None

class DefaultsConfig(BaseModel):
    license: str = "CC-BY-4.0"
    providers: List[Provider] = []
    geometry: Optional[Dict] = None

class TemplateConfig(BaseModel):
    type: Literal['catalog', 'collection', 'item']
    output_path: str
    include_sample_item: bool = True

class ScaffoldConfig(BaseModel):
    mode: Literal['items', 'collection', 'catalog'] = 'items'
    collection_id: Optional[str] = None
    base_url: Optional[HttpUrl] = None
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    template: Optional[TemplateConfig] = None
```

### 3.1 Example Usage (YAML)

```yaml
- id: scaffold
  module: ScaffoldModule
  config:
    mode: items
    collection_id: "landsat-c2-l2"
    defaults:
      license: "PDDL-1.0"
      providers:
        - name: "USGS"
          roles: ["producer", "licensor"]
```

## 4. I/O Contract

**Input (Workflow Context)**:
- `transform` (or prev step): `Iterator[TransformedItem]`

**Output (Python)**:
```python
def modify(self, item: dict, context: WorkflowContext) -> dict | None:
    """
    Wraps raw dictionary into a valid STAC Item dictionary.
    """
```

## 5. Error Handling
- **Missing Mandatory Field**: If input dict lacks `datetime` or `geometry` (and no default), skip and log failure.
- **Invalid ID**: Sanitize or fail if ID contains invalid characters.
