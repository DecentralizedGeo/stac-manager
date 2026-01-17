# Specification Feedback Response

## Summary of Changes Based on User Feedback

This document addresses all feedback points raised during specification review.

---

## Technical Architecture Specification Changes

### 1. ✅ **DAG Definition Clarified**

**Your Question**: "What do we mean by DAGs?"

**Change Made**: Added full explanation in Workflow Orchestrator section:
> "The orchestrator is the central component that builds and executes workflow **DAGs (Directed Acyclic Graphs)** from YAML configuration files. A DAG is a graph structure where workflow steps are nodes and dependencies are directed edges, with no circular dependencies."

---

### 2. ✅ **IngestModule Dependency Clarified**

**Your Comment**: "I'm guessing running the DiscoveryModule is a functional requirement to run before running this module?"

**Change Made**: Added dependency note to IngestModule:
- Can run standalone if `collection_ids` are provided in config
- Typically depends on `DiscoveryModule` to get Collection objects from context
- Added `collection_ids` option to config for direct collection specification

---

### 3. ✅ **Item-Level Filters Added**

**Your Comment**: "We should also be able to apply filters at the Item level... treat optional filters for collection and items differently"

**Changes Made**:
- Added Item-level filter support to IngestModule inputs
- Filters include temporal, spatial, and query parameters (CQL2)
- Explicitly noted: "Supports Item-level filters separate from Collection-level filters"
- Example: Filter Collections broadly, then filter Items specifically (e.g., cloud cover < 10%)

**YAML Config Example**:
```yaml
- id: ingest
  module: IngestModule
  config:
    filters:
      temporal:
        start_date: "2024-01-01T00:00:00Z"
        end_date: "2024-12-31T23:59:59Z"
      spatial:
        bbox: [-180, -90, 180, 90]
      query:
        "properties.eo:cloud_cover": {"lt": 10}
```

---

### 4. ✅ **ScaffoldModule Enhanced for Collections and Templates**

**Your Comments**: 
- "What if I want to scaffold a blank template? Either a catalog, collection, or an item?"
- "While this module 'scaffolds' items, what about collections?"

**Changes Made**:
- Updated purpose to include Collections and Catalogs
- Added `mode` parameter: `items | collection | catalog | template`
- **Template Mode**: Generate empty STAC objects for manual editing
- **Collection Scaffolding**: Can scaffold Collections with proper structure

**YAML Config Example**:
```yaml
- id: scaffold_template
  module: ScaffoldModule
  config:
    mode: template
    template:
      type: collection  # or catalog, or item
      output_path: ./templates/my-collection-template.json
```

---

### 5. ✅ **Geometry Defaults Supported**

**Your Comment**: "What if the transformed data doesn't have any geometry? Could we apply a default?"

**Change Made**: Added geometry default support to ScaffoldModule:
- Supports `null` geometry for non-spatial Items
- Allows configurable default geometry (e.g., default bounding box)

**YAML Config Example**:
```yaml
- id: scaffold
  module: ScaffoldModule
  config:
    defaults:
      geometry: null  # or specify a default polygon
      license: "CC0-1.0"
      providers: [...]
```

---

### 6. ✅ **Link Generation Clarified**

**Your Comment**: "I'm guessing the links will be relative?"

**Change Made**: Explicitly documented link generation behavior:
- **Relative by default**: `./collection.json`, `../items/item-001.json`
- **Absolute if `base_url` provided**: `https://example.com/stac/collection.json`

---

### 7. ✅ **Field Defaults in ScaffoldModule**

**Your Comment**: "Should we be able to specify and set default values for fields in YAML config?"

**Change Made**: Added `defaults` section to ScaffoldModule config:
- Can set default values for optional STAC fields
- Examples: default license, providers, geometry
- Prevents need to transform every field; can scaffold with sensible defaults

---

## API/Interface Specification Changes

### 8. ✅ **UpdateModule Input Sources Clarified**

**Your Comment**: "The input format would be a json or parquet file? I'd assume when modifying, it's for STAC Items that exist on disk"

**Change Made**: Clarified UpdateModule can:
- Load from `source_file` (JSON/Parquet on disk)
- **OR** use Items from previous workflow step via `depends_on`

**YAML Example**:
```yaml
- id: update
  module: UpdateModule
  config:
    source_file: ./output/items.parquet  # Load from disk
    updates:
      properties.updated: "{now}"
```

---

### 9. ✅ **Multiple Workflows Addressed**

**Your Comment**: "Can we define multiple workflows in the configuration?"

**Change Made**: Added NOTE in API spec:
> **Multiple Workflows**: Currently, each YAML file defines a single workflow. To run different workflows, use separate YAML files and specify via `--config` flag. Future versions may support multiple workflow definitions in a single file with workflow selection.

**Current Approach**: Use separate files for different workflows
- `workflow-ingest.yaml`
- `workflow-update.yaml`
- `workflow-validate.yaml`

---

### 10. ✅ **STAC Best Practices for Directory Structure**

**Your Important Comments on Item Layout**:
- "Items should be stored in subdirectories... if there are usually sidecar files"
- "Unless there are additional files to store alongside a given item, group items into a directory with name representing the item id"

**Changes Made**: Updated JSON output file structure to follow [STAC Best Practices](https://github.com/radiantearth/stac-spec/blob/master/best-practices.md#catalog-layout):

**New Structure** (organize_by: collection):
```
output/
├── catalog.json
├── collection_A/
│   ├── collection.json
│   ├── item_001/              # Item subdirectory (named by ID)
│   │   └── item_001.json
│   ├── item_002/
│   │   └── item_002.json
│   └── ...
```

Added note explaining when to use flat vs. subdirectory structure:
- Use subdirectories if workflow generates sidecar files (thumbnails, metadata)
- Use `organize_by: flat` if no sidecar files needed

---

## Remaining Questions / Design Discussions

### DiscoveryModule for Items?

**Your Comment**: "How much does complexity increase if we add ability to discover items? Or is that the purpose of IngestModule?"

**Answer**: 
- **DiscoveryModule**: Focused on discovering **Collections** from STAC APIs
- **IngestModule**: Focused on discovering/fetching **Items** from Collections
- Separation of concerns keeps modules focused and testable

**Rationale**: 
- Discovery workflow: Find Collections → Filter Collections → Fetch Items from Collections
- IngestModule already handles Item discovery via `Client.search()`
- Adding Item discovery to DiscoveryModule would duplicate functionality

**However**, if you have a use case where you need to discover Items across multiple catalogs without going through Collections first, we could discuss adding this capability.

---

## Summary Table of Changes

| # | Topic | Status | Spec Updated |
|---|-------|--------|--------------|
| 1 | DAG definition clarified | ✅ Complete | Technical Arch |
| 2 | IngestModule dependency note | ✅ Complete | Technical Arch |
| 3 | Item-level filters | ✅ Complete | Both |
| 4 | Collection scaffolding | ✅ Complete | Both |
| 5 | Geometry defaults | ✅ Complete | Both |
| 6 | Link generation clarified | ✅ Complete | Technical Arch |
| 7 | Field defaults in scaffold | ✅ Complete | Both |
| 8 | UpdateModule input sources | ✅ Complete | API/Interface |
| 9 | Multiple workflows note | ✅ Complete | API/Interface |
| 10 | STAC best practices (directories) | ✅ Complete | API/Interface |
| 11 | DiscoveryModule for Items | 💬 Discussion | - |

---

## Next Steps

With these refinements incorporated, the specifications are now ready for implementation planning. The specifications address:

✅ All architectural concerns  
✅ User feedback on best practices  
✅ Configuration flexibility  
✅ Module capability enhancements  
✅ Clear I/O contracts  

Please let me know if:
1. Any of these changes need further refinement
2. You'd like to discuss the DiscoveryModule/Items question
3. You're ready to proceed to implementation planning
