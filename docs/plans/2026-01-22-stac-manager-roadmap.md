# STAC Manager Implementation Roadmap
**Date**: 2026-01-22  
**Status**: Phase 1 In Progress

---

## Vision

**STAC Manager** is a standalone Python library for building, orchestrating, and executing modular STAC data pipelines. It enables users to:
- Ingest STAC items from APIs or files
- Transform and enrich metadata
- Validate STAC compliance
- Apply extensions
- Output to various formats (Parquet, JSON, etc.)

All through declarative YAML configuration or programmatic Python API.

---

## Phased Implementation Strategy

### Phase 1: Utilities Foundation ⏳ **(CURRENT)**

**Goal**: Build the foundational utility layer that all higher-level components will depend on.

**Scope**: `stac_manager/utils/`
- `serialization.py` - PySTAC ↔ dict conversion
- `field_ops.py` - Field manipulation (dot notation, JMESPath, deep_merge)
- `geometry.py` - Spatial operations (bbox, validation)
- `streaming.py` - Async iterator helpers
- `validation.py` - STAC validation and item hydration

**Why First**: 
- Establishes core patterns (dict wire format, error handling)
- Provides building blocks for modules
- Can be tested in isolation
- Enables external users to leverage utilities standalone

**Dependencies**: None (only external: PySTAC, Shapely, JMESPath)

**Success Criteria**:
- ✅ All 5 utility modules implemented
- ✅ ≥90% test coverage
- ✅ Three-tier error handling (Fail Fast, Step Out, Graceful Degradation)
- ✅ Public API documented (`__all__` exports)
- ✅ Type-safe (mypy passes)

**Deliverables**:
- [Design Document](./2026-01-22-stac-manager-phase-1-utilities-design.md)
- [Implementation Plan](./2026-01-22-stac-manager-phase-1-utilities-specification.md)
- Working `stac_manager/utils/` package

**Estimated Duration**: 2-3 days (18 granular TDD tasks)

---

### Phase 2: Pipeline Modules ✅ **Completed**

**Goal**: Implement the specialized pipeline components that perform domain-specific STAC operations.

**Scope**: `stac_manager/modules/`

**Modules to Implement** (in dependency order):

#### 2.1 Fetchers (Sources)
- **`IngestModule`** - Fetch items from STAC API or files
  - API mode: pystac-client + async HTTP
  - File mode: Read from Parquet/JSON
  - Internal parallelism via temporal splitting
- **`SeedModule`** - Generate skeleton items for scaffolding
  - Static item lists
  - File-based item loading

#### 2.2 Modifiers (Processors)
- **`TransformModule`** - Join sidecar data and map fields
  - Sidecar indexing and enrichment
  - JMESPath mapping (uses `utils/field_ops.py`)
  - Merge strategies
- **`UpdateModule`** - Modify existing STAC fields
  - Dot notation updates (uses `utils/field_ops.py`)
  - Patch application
  - Timestamp management
- **`ExtensionModule`** - Apply STAC extensions
  - Generic extension application
  - Extension validation
- **`ValidateModule`** - STAC schema validation
  - stac-validator integration (uses `utils/validation.py`)
  - Strict vs. permissive modes

#### 2.3 Bundlers (Sinks)
- **`OutputModule`** - Write to Parquet/JSON
  - Batch buffering
  - Atomic writes
  - stac-geoparquet integration

**Dependencies**: Phase 1 (utilities must exist)

**Success Criteria**:
- All protocols implemented (`Fetcher`, `Modifier`, `Bundler`)
- Each module has comprehensive tests
- Modules use utilities from Phase 1
- Integration tests demonstrate module interop

**Key Decisions Needed**:
- Module registration mechanism
- Configuration validation patterns
- Error propagation between modules

**Estimated Duration**: 5-7 days

---

### Phase 3: Orchestration Layer ✅ **Completed**

**Goal**: Build the workflow engine that wires modules together and manages execution.

**Scope**: `stac_manager/core/`

**Components**:

#### 3.1 Core Infrastructure
- **`WorkflowContext`** - Shared execution state
  - Logger, FailureCollector, Checkpoints
  - Inter-step data (`context.data`)
- **`FailureCollector`** - Error aggregation
  - Failure records with context
  - JSON reporting
- **`CheckpointManager`** - State persistence
  - Resume from failure
  - Atomic state snapshots

#### 3.2 Configuration System
- **`WorkflowDefinition`** (Pydantic model)
  - YAML loading and validation
  - Matrix strategy expansion
  - Dependency resolution
- **`VariableSubstitutor`** - Environment variable substitution
  - Recursive substitution with type inference
  - Priority: context > env

#### 3.3 Orchestration Engine
- **`StacManager`** - Main orchestrator
  - Module loading and instantiation
  - Pipeline execution (async loop)
  - Matrix strategy parallelization
  - Graceful shutdown and cleanup
- **`PipelineExecutor`** - Execution engine
  - Wire Fetchers → Modifiers → Bundlers
  - Stream management
  - Error handling and recovery

#### 3.4 CLI & API
- **CLI** (`stac_manager.cli`)
  - `stac-manager run workflow.yaml`
  - Progress reporting
  - Logging configuration
- **Python API**
  - Programmatic workflow building
  - Direct module usage (bypass YAML)

**Dependencies**: Phase 1 + Phase 2

**Success Criteria**:
- End-to-end workflows execute successfully
- Matrix strategy works (parallel pipelines per collection)
- Failures are collected and reported
- State can be restored from checkpoints
- CLI provides good UX

**Key Decisions Needed**:
- Module discovery/registration strategy
- Plugin architecture for custom modules
- Async vs. sync boundaries in orchestrator

**Estimated Duration**: 7-10 days

---

## Cross-Cutting Concerns

### Error Handling (All Phases)

**Three-Tier Model** (established in Phase 1, enforced throughout):

1. **Tier 1: Fail Fast** - Configuration/startup errors
   - Raises `ConfigurationError`
   - Workflow aborts before execution
   
2. **Tier 2: Step Out** - Item-level non-critical errors
   - Logged to `FailureCollector`
   - Pipeline continues
   - Functions return `bool` or `Optional[T]`
   
3. **Tier 3: Graceful Degradation** - Optional features
   - Fallback behavior
   - Warning logged but processing continues

### Testing Strategy (All Phases)

- **TDD**: RED-GREEN-REFACTOR for all features
- **No domain mocks**: Real STAC items/geometries
- **Mock infrastructure**: HTTP, file I/O, WorkflowContext
- **Coverage**: ≥90% on all modules
- **Integration tests**: End-to-end workflow validation

### Documentation (All Phases)

Each phase produces:
- Design document (architectural decisions)
- Implementation plan (granular TDD tasks)
- API documentation (docstrings + examples)
- User guide updates (as features complete)

---

## Current Status

### Phase 1: Utilities Foundation
- [x] Research findings documented
- [x] Design validated with user
- [x] Implementation plan created (18 tasks)
- [x] Task 1 - Test fixtures
- [x] Tasks 2-18: Module implementation
- [x] Verification and coverage validation

### Phase 2: Pipeline Modules
- [x] ✅
- **Prerequisite**: Phase 1 complete

### Phase 3: Orchestration Layer
- [x] ✅
- **Prerequisite**: Phase 1 + Phase 2 complete

---

## Success Metrics (Full Implementation)

### Functional
- Users can define workflows in YAML
- Workflows execute successfully for 1M+ item catalogs
- Memory usage remains constant (streaming)
- Failures are collected and reportable
- CLI provides intuitive UX

### Technical
- ≥90% test coverage across all packages
- Type-safe (mypy passes)
- Pristine test output (no warnings)
- Performance: >1000 items/sec for simple transforms

### Maintainability
- Clear module boundaries
- Comprehensive documentation
- Easy to add new modules (plugin pattern)
- Debug-friendly (good logging, error messages)

---

## References

### Specifications
- [System Overview](../spec/stac-manager-v1.0.0/00-system-overview.md)
- [Pipeline Management](../spec/stac-manager-v1.0.0/01-pipeline-management.md)
- [Protocols](../spec/stac-manager-v1.0.0/06-protocols.md)
- [Data Contracts](../spec/stac-manager-v1.0.0/05-data-contracts.md)
- [Module Specs](../spec/stac-manager-v1.0.0/modules/)

### Phase 1 Documents
- [Utilities Design](./2026-01-22-stac-manager-phase-1-utilities-design.md)
- [Implementation Plan](./2026-01-22-stac-manager-phase-1-utilities-specification.md)
- [Research Findings](../../../../../.gemini/antigravity/brain/b37745a6-e746-44a5-a76f-65581571d971/research-findings.md)
