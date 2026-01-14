# Project Requirements Document (PRD)

## STAC Catalog Manager

**Project**: STAC Catalog Manager — A comprehensive Python toolkit for building, managing, and extending STAC catalogs at scale.

**Version**: 1.0.2 (v1 PRD - Updated with EOEPCA Integration)  
**Status**: Draft  
**Last Updated**: January 12, 2026

---

## Table of Contents

- [Project Requirements Document (PRD)](#project-requirements-document-prd)
  - [STAC Catalog Manager](#stac-catalog-manager)
  - [Table of Contents](#table-of-contents)
  - [Executive Summary](#executive-summary)
  - [Project Vision \& Goals](#project-vision--goals)
    - [Vision Statement](#vision-statement)
    - [Primary Goals](#primary-goals)
  - [Integration Points](#integration-points)
    - [1. STAC API v1.0.0 Endpoints](#1-stac-api-v100-endpoints)
    - [2. pgstac / stac-fastapi-pgstac](#2-pgstac--stac-fastapi-pgstac)
    - [3. Validation Integration](#3-validation-integration)
    - [4. File I/O Integration](#4-file-io-integration)
    - [5. EOEPCA STAC Utilities Integration](#5-eoepca-stac-utilities-integration)
  - [Appendix A: Reference Links](#appendix-a-reference-links)
  - [Appendix B: Glossary](#appendix-b-glossary)
  - [Summary of Changes (v1.0 → v1.1)](#summary-of-changes-v10--v11)
    - [Key Updates](#key-updates)
    - [Rationale](#rationale)

---

## Executive Summary

**STAC Catalog Manager** is an open-source Python toolkit designed to simplify the creation, modification, and management of STAC (SpatioTemporal Asset Catalog) metadata at scale. The primary goal is to reduce complexity and friction in STAC workflows—enabling users to scaffold, ingest, extend, and maintain STAC catalogs (Collections, Items) from diverse sources (CMR-STAC, other STAC APIs, non-STAC APIs, local data files).

This toolkit builds upon and complements existing STAC ecosystem tools, particularly the **EOEPCA stac-cat-utils** library, by providing a higher-level orchestration layer optimized for production workflows and operational scale.

**Key Capabilities:**

- Bulk ingestion from STAC APIs (CMR-STAC, STAC Index catalogs, etc.)
- Metadata transformation & field mapping (JSON, CSV, Parquet, etc.)
- STAC Item scaffolding and bulk creation
- Extension application (dgeo, alternate-assets, and pluggable custom extensions)
- Metadata updates and deletion
- Incremental and full catalog rebuilds
- Asynchronous, parallelized processing for performance at scale (800K+ Items)
- CLI + library interfaces for both direct use and Docker containerization

**Success Metric:** Simplify the management workflows (creation, modification, extension) of STAC metadata by reducing operational friction through a composable, maintainable, and extensible toolkit.

---

## Project Vision & Goals

### Vision Statement

Empower users and organizations to confidently build, maintain, and extend large-scale STAC catalogs by providing a flexible, modular Python toolkit that handles the repetitive, error-prone aspects of metadata management.

### Primary Goals

1. **Workflow Simplification**: Reduce operational complexity in creating and managing STAC catalogs through composable, well-documented tools.

2. **Reusability & Extensibility**: Design the toolkit as an open-source library/CLI usable by diverse organizations and use cases, not just internal pipelines.

3. **Multi-Source Ingestion**: Support ingestion from multiple sources (STAC APIs, non-STAC APIs, local files) with flexible transformation logic.

4. **Extension Support**: Provide pluggable module architecture for STAC extensions (dgeo, alternate-assets, etc.) to reduce coupling and enable custom extensions.

5. **Scale & Performance**: Handle 800K+ Items efficiently through asynchronous operations, parallelization, and rate-limited API access.

6. **Reliable Partial Processing**: Log failures gracefully, flag problematic Items, and allow workflows to continue rather than failing entirely.

7. **Spec-Driven Development**: Design the toolkit with clear specifications and acceptance tests to enable coding agents to implement and extend features.

8. **Ecosystem Integration**: Build upon existing EOEPCA tools (stac-cat-utils) and STAC ecosystem libraries to avoid duplication and maximize interoperability.

---

## Integration Points

### 1. STAC API v1.0.0 Endpoints

The toolkit acts as a client to standard STAC v1.0.0 API endpoints:

- **CMR-STAC**: <https://cmr.earthdata.nasa.gov/stac/v1>
- **STAC Index**: <https://stacindex.org> (catalog registry, not direct API)
- **Custom STAC APIs**: Any endpoint implementing STAC API v1.0.0

**Expected Endpoints**:

- `GET /` – Root catalog
- `GET /collections` – List collections
- `GET /collections/{id}` – Collection metadata
- `GET /collections/{id}/items` – Items with pagination
- `GET /search` – Search endpoint (optional, may be used for advanced filtering)

---

### 2. pgstac / stac-fastapi-pgstac

The toolkit generates metadata **compatible with pgstac ingestion**:

- **Output Formats**: JSON or Parquet (pgstac can ingest from these)
- **No Direct DB Access**: Toolkit does not write to pgstac database; it produces files for external ingestion
- **Future Integration**: A separate step (pgstac CLI or API call) ingests the generated metadata

---

### 3. Validation Integration

- **stac-validator**: Python package for STAC v1.1.0 validation
- **Extension Schemas**: Load from upstream (DecentralizedGeo, STAC extensions repo) or local
- **Custom Validation**: Users can provide custom JSON schema files

---

### 4. File I/O Integration

**Supported Input Formats**:

- JSON (array of objects or single object)
- CSV (with header row)
- Parquet (columnar)
- Streams from STAC API

**Supported Output Formats**:

- JSON (pretty-printed)
- Parquet (with schema preservation)

**Libraries**:

- `pandas` (CSV, Parquet I/O)
- `pyarrow` (Parquet)
- `json` (standard library)

---

### 5. EOEPCA STAC Utilities Integration

The toolkit integrates with and builds upon the existing **EOEPCA stac-cat-utils** library, which provides foundational utility functions for STAC metadata manipulation in Python.

**Complementary Relationship**:

| Layer | Component | Responsibility |
|-------|-----------|----------------|
| **Low-Level Utilities** | stac-cat-utils (existing) | Reusable functions for STAC operations: metadata parsing, validation helpers, common transformations |
| **Orchestration Layer** | STAC Catalog Manager (this toolkit) | Production-ready workflows: CLI interfaces, async/parallel processing, configuration-driven composition, pluggable extensions, comprehensive logging |

**Toolkit Capabilities Built on Top**:

- CLI and programmatic interfaces
- Asynchronous processing and rate limiting for scale (800K+ items)
- Workflow configuration and composition (YAML/JSON configs)
- Pluggable extension architecture
- Comprehensive logging and error recovery
- Docker containerization for operational deployment

**Integration Strategy**:

- Leverage `stac-cat-utils` for foundational STAC operations where applicable
- Build additional orchestration, scaling, and CLI layers on top
- Maintain compatibility with EOEPCA ecosystem standards
- Contribute improvements back to shared utilities where beneficial

**Benefits of This Approach**:

- No duplication of low-level utilities
- Clear separation of concerns (utilities vs. orchestration)
- Complementary role within EOEPCA platform evolution
- Potential for shared maintenance and community contributions
- Leverages proven EOEPCA code where applicable

**References**:

- Repository: <https://github.com/EOEPCA/stac-cat-utils>
- STAC Index: <https://stacindex.org/ecosystem?language=Python>
- EOEPCA Project: <http://eoepca.org/>
- EOEPCA Documentation: <https://eoepca.readthedocs.io>

---

## Appendix A: Reference Links

- **STAC Spec v1.1.0**: <https://github.com/radiantearth/stac-spec/releases/tag/v1.1.0>
- **STAC API Spec v1.0.0**: <https://github.com/radiantearth/stac-api-spec/>
- **CMR-STAC**: <https://github.com/nasa/cmr-stac>
- **stac-validator**: <https://github.com/stac-utils/stac-validator>
- **dgeo Extension**: <https://github.com/DecentralizedGeo/dgeo-asset>
- **alternate-assets Extension**: <https://github.com/stac-extensions/alternate-assets>
- **RFC 3339**: <https://tools.ietf.org/html/rfc3339>
- **STAC Index**: <https://stacindex.org>
- **Astral API**: <https://github.com/DecentralizedGeo/astral-api>
- **pgstac**: <https://github.com/stac-utils/pgstac>
- **stac-fastapi-pgstac**: <https://github.com/stac-utils/stac-fastapi-pgstac>
- **EOEPCA Project**: <http://eoepca.org/>
- **EOEPCA Documentation**: <https://eoepca.readthedocs.io>
- **EOEPCA stac-cat-utils**: <https://github.com/EOEPCA/stac-cat-utils>
- **STAC Ecosystem (Python)**: <https://stacindex.org/ecosystem?language=Python>

---

## Appendix B: Glossary

| Term | Definition |
|------|-----------|
| **STAC** | SpatioTemporal Asset Catalog — a specification for describing geospatial data |
| **Item** | A STAC entity representing a single asset or collection of assets at a specific place/time |
| **Collection** | A STAC entity grouping related Items |
| **Catalog** | A STAC entity linking Collections and Items hierarchically |
| **Extension** | Additional metadata fields following a defined schema (e.g., dgeo, alternate-assets) |
| **CMR** | Common Metadata Repository — NASA's Earth Science metadata catalog |
| **pgstac** | PostgreSQL-based STAC catalog implementation |
| **RFC 3339** | Standard format for date/time representation (ISO 8601 profile) |
| **GeoJSON** | JSON-based format for geospatial features |
| **Parquet** | Columnar data format optimized for analytics |
| **Rate Limiting** | Controlling the number of API requests to avoid overwhelming servers |
| **Async I/O** | Asynchronous input/output for concurrent operations |
| **Materialization** | The process of fetching and persisting metadata |
| **Transformation** | Converting metadata from one format/schema to another |
| **Validation** | Checking metadata compliance with schemas/standards |
| **EOEPCA** | Earth Observation Exploitation Platform Common Architecture |
| **stac-cat-utils** | EOEPCA utility library providing foundational STAC operations |

---

**End of Document**

---

## Summary of Changes (v1.0 → v1.1)

### Key Updates

1. **Executive Summary**: Added acknowledgment of EOEPCA stac-cat-utils as foundational library
2. **Project Goals**: Added "Ecosystem Integration" as goal #8
3. **Integration Points**: Added comprehensive Section 5 on EOEPCA STAC Utilities Integration
4. **Architecture**: Updated design principles to include ecosystem reuse
5. **References**: Added EOEPCA project and stac-cat-utils links
6. **Glossary**: Added EOEPCA and stac-cat-utils definitions

### Rationale

- Positions toolkit as orchestration layer, not standalone solution
- Acknowledges existing EOEPCA infrastructure
- Signals collaboration intent within ecosystem
- Clarifies unique value proposition (production workflows + scale)
- Enables code reuse and reduces duplication
