# Semantic Memory: STAC Manager Concepts

## Core Abstractions
- **Pipes and Filters**: The fundamental architectural pattern. Components are "Filters" (Fetchers, Modifiers, Bundlers) connected by "Pipes" (the orchestration engine).
- **Fetcher (Async Source)**: Handles high-concurrency I/O (STAC APIs, S3).
- **Modifier (Sync Filter)**: Performs item-level logic (Transform, Update). Kept sync for CPU efficiency and developer simplicity.
- **Bundler (Sync/Async Sink)**: Aggregates and serializes items (Parquet, JSON).

## Tooling Context
- **PySTAC**: The foundation library for all data models.
- **pystac-client**: Primary engine for API-based fetchers.
- **stac-geoparquet**: Used by Bundlers for optimized spatial storage.
## STAC Manager Architecture
- **Phase 1: Utilities Foundation**: Foundational layer (`stac_manager/utils/`) for field manipulation, geometry processing, and streaming.
- **Phase 2: Pipeline Modules**: Domain-specific filters (Ingest, Transform, etc.) built on utils.
- **Phase 3: Orchestration Layer**: The workflow engine connecting modules.

## Data Structure Policies
- **Wire Format**: Items flow through the pipeline as pure `dict` for performance and stability.
- **Serialization**: Conversion to PySTAC objects is only done at I/O boundaries or where rich API is required.
