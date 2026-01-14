# STAC Ecosystem Tool Evaluation

**Date:** 2026-01-12
**Context:** Researching existing tools to inform the architecture of `dgeo-stac-utils`.

## 1. Summary Recommendations

| Tool | Recommendation | Role in `dgeo-stac-utils` |
| :--- | :--- | :--- |
| **PySTAC** | **MUST USE** | Core data model for Items/Collections/Catalogs. |
| **PySTAC-Client** | **MUST USE** | Fetching metadata from CMR-STAC and other upstream APIs. |
| **stac-validator** | **MUST USE** | Validation of generated Items and extension schemas. |
| **stactools** | **ADOPT PATTERN** | adopt the "CLI + Packages" architecture. Use core utilities if stable. |
| **stac-geoparquet** | **INTEGRATE** | Critical for handling the 800k+ item scale in bulk outputs. |
| **stac-asset** | **UTILITY** | Helper for downloading assets when computing CIDs/multihashes. |
| **stackstac** | *SKIP* | Focused on analysis/xarray; not relevant for catalog *creation*. |
| **intake-stac** | *SKIP* | Focused on consumption; redundant with PySTAC-Client for our needs. |
| **pygeometa** | *SKIP* | Too generic; PySTAC is better suited for pure STAC workflows. |

---

## 2. Detailed Analysis

### 2.1. Core Libraries

#### [PySTAC](https://pystac.readthedocs.io/)

* **Status:** Active, Industry Standard.
* **Relevance:** 10/10.
* **Analysis:** This is the foundational library for the entire ecosystem. It handles serialization, validation, and the object model.
* **Decision:** We will build strictly on top of PySTAC classes (`Item`, `Asset`, `Collection`). The `dgeo` extension will be implemented as a custom PySTAC Extension.

#### [PySTAC-Client](https://pystac-client.readthedocs.io/)

* **Status:** Active.
* **Relevance:** 9/10.
* **Analysis:** Essential for the "Fetch" phase of our pipeline. It handles pagination and search abstraction against CMR-STAC.
* **Decision:** Use this to query source APIs. It abstracts away the complexity of "iterating over pages of results."

#### [stac-validator](https://github.com/stac-utils/stac-validator)

* **Status:** Active.
* **Relevance:** 10/10.
* **Analysis:** The standard tool for validating STAC JSON against schemas. It supports checking both core spec and extensions.
* **Decision:** Integrate strictly for the "Validation" phase to ensure all output is compliant before it leaves the tool.

### 2.2. Tooling & workflows

#### [stactools](https://stactools.readthedocs.io/)

* **Status:** User noted potentially stale (last major update ~2023).
* **Relevance:** 8/10 (Architecture), 5/10 (Direct Dependency).
* **Analysis:**
  * **Pros:** Defines a clear standard for "Packages" (plugins) that convert raw data -> STAC. This matches our "Swiss Army Knife" goal.
  * **Cons:** If maintenance is slowing, heavy reliance might be risky.
* **Decision:** **Borrow the Pattern.** We should structure `dgeo-stac-utils` similarly: a core CLI that dispatches to "loaders" or "commands." We can check if `stactools` itself is stable enough to serve as the CLI runner, but given we have specific `dgeo` needs, a custom `click` or `typer` CLI (like `stactools` uses under the hood) might be cleaner.

#### [stac-asset](https://github.com/stac-utils/stac-asset)

* **Status:** Active.
* **Relevance:** 7/10.
* **Analysis:** Handles the messy business of downloading assets (handling retries, auth, etc.).
* **Decision:** Use this when we need to physically download a file to compute its CID (Content Identifier) for the `dgeo` extension.

#### [stac-geoparquet](https://github.com/stac-utils/stac-geoparquet)

* **Status:** Emerging Standard.
* **Relevance:** 9/10 (for scale).
* **Analysis:** JSON is slow at 800k items. `pgstac` supports massive scale, but for intermediate storage or "bulk dumps," GeoParquet is superior.
* **Decision:** Include `stac-geoparquet` export as a first-class output format alongside `pgstac` ingestion.

### 2.3. Consumption & Analysis (Lower Priority)

#### [stackstac](https://stackstac.readthedocs.io/) & [intake-stac](https://intake-stac.readthedocs.io/)

* **Relevance:** Low.
* **Analysis:** These tools are for *users* who want to load data into Python/Pandas/Xarray for analysis.
* **Decision:** We are *building* the catalog, not just consuming it. We might use them in our "Verification" scripts to prove the catalog is usable, but they aren't core dependencies for the builder.

#### [pygeometa](https://geopython.github.io/pygeometa/)

* **Relevance:** Low.
* **Analysis:** Great for generating ISO 19115 XML from MCF configs. Unless we need to export legacy XML metadata from our STAC items, this is unnecessary. PySTAC handles the JSON generation better.
