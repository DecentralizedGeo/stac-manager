# Initial Design Questions for the PRD

The questions below were generated based on the initial design of this project to as assist in the creation of the PRD.

## 1. Overall Goals and Scope

1. What is the primary “success metric” for this project (e.g., throughput, completeness of metadata, ease of extension, stability, developer UX, something else)? (A) Primary "success metric" is simplifying the management (e.g. creation, modification) workflows of STAC metadata (e.g. Catalogs, Collections, Items).

2. Is the tool intended mainly for one-off bulk catalog creation, or for continuous/recurring synchronization with CMR-STAC (e.g., daily/weekly updates)? (A) It's intended for various use cases; 1. one-off bulk creation 2. scaffold new STAC metadata (any or all STAC components (e.g. Catalogs, Collections, Items)) that follows the [STAC Spec](https://github.com/radiantearth/stac-api-spec/blob/release/v1.0.0/stac-spec/overview.md) 3. Bulk updates to existing metadata 4. Extend STAC metadata with additional extension metadata fields. 5. Clone and or copy existing STAC components from a STAC API endpoint, like the CMR-STAC or any existing catalogs that are found on [STAC Index](https://stacindex.org/catalogs) 6. Continuous/recurring synchronization of new content to existing STAC catalogs. 7. Onboarding new catalogs and transforming non-standard STAC sources (e.g. API endpoints like the [Astral API](https://github.com/DecentralizedGeo/astral-api)) into STAC compliant metadata. 8. Modify existing STAC metadata, either by updating the metadata or removing it.

3. Do you envision this as a reusable open-source library/CLI others will use, or a one-off internal pipeline tailored to your specific collections? (A) It's intended to be a reusable open-source library/CLI others will use. We don't need to hit every edge case, but we do need to be able to handle uses cases for the `dgeo` extension.

***

## 2. Input Data & Target Collections

1. How will you specify which CMR-STAC Collections to ingest (explicit list of IDs, provider prefixes, temporal/spatial filters, etc.)? (A) Specify a given catalog URL and a list of collections to ingest from that catalog. It should support filtering like temporal and spatial filters.

2. Are all ~800K items coming from a known fixed set of CMR-STAC Collections, or could that set evolve over time? (A) Yes, the set of collections I mentioned will come from an existing set of collections but the set of items in the collection can evolve over time.

3. Are there any non–CMR-STAC sources you intend to ingest into the same catalog (e.g., other STAC APIs, local assets, CSV/JSON manifests)? (A) By "non–CMR-STAC sources" do you mean metadata that would be used to hydrate existing or additional metadata fields? If yes, that is to be expected.  I'll have content, in the form of JSON files, csv files, geoparquet/parquet files, etc and/or also ingested from other STAC APIs and non-STAC APIs (such as the [Astral API](https://github.com/DecentralizedGeo/astral-api)). I'll need to figure out how to transform the data into STAC metadata using some kind of field mapping strategy. That could be driven by some kind of schema or metadata configuration file (yaml or json).

***

## 3. STAC Item Requirements

1. For the “minimum viable” STAC Item, do you want to strictly follow the baseline STAC 1.0.0 Item spec, or include some extensions (e.g., `proj`, `eo`, `sar`, `raster`) from the start? (A) Follow the baseline STAC 1.0.0 Item spec. Specifying extensions to extend the STAC Item spec can be done as a seperate process.
2. Do you have a canonical mapping (even informal) of CMR fields → STAC core properties/links/assets, or should the PRD define that mapping strategy? (A) Can you expand on this? Are you asking for how we should map the "source" fields to the "destination" fields?
3. Are there any non-standard or project-specific properties you know you’ll want on every Item (e.g., internal IDs, lineage, quality flags)? (A) None that I can think of at the moment.

***

## 4. Extensions: dgeo & alternate-assets

1. What are the key fields from the `dgeo` extension you know you must support initially (e.g., ownership, licensing, tokenization, provenance)? (A) Here is the link to the [dgeo extension schema](https://raw.githubusercontent.com/DecentralizedGeo/dgeo-asset/refs/heads/pgstac-variant/json-schema/schema.json)
2. For `alternate-assets`, what use cases are you targeting (e.g., mirror locations, different access protocols, different formats, different cost tiers)? (A) For now, supporting alternate locations for retrieval for the same asset is the primary use case.
3. Do you need the initial PRD to support pluggable extension modules (e.g., easy to add more extensions later) or can it hard-code dgeo + alternate-assets to start? (A) Let's try to make it flexible enough to support pluggable modules that are extension focused e.g. dgeo, alternate-assets, etc.

***

## 5. Interaction with pgstac / stac-fastapi-pgstac

1. Will this tool write directly to the pgstac database (via SQL / psycopg) or generate STAC JSON that another process will ingest? (A) The generated STAC metadata can be saved to a parquet file or JSON that can be ingested by pgstac in another process.
2. Are there constraints from your existing pgstac deployment (schema version, available hardware, max batch sizes, transaction limits) that should shape the design? (A) I'm not aware of any constraints at the moment.
3. Do you want the tool to support both:
    - (a) full catalog rebuilds, and  
    - (b) incremental updates (new/modified/deleted Items),
    or just one of these? (A) Support both full catalog rebuilds and incremental updates.

***

## 6. “Swiss Army Knife” Architecture

1. How do you imagine the tools being composed: a CLI with subcommands, a Python library with functions/classes, or both? (A) What do you recommend as the best way to compose the tools that makes it maintainable and extensible? Ideally, decreasing coupling between the components is a priority, making it easier to swap out components as needed.
2. What are some concrete “tasks” you already foresee (e.g., `discover-collections`, `fetch-items`, `normalize-item`, `apply-extensions`, `validate`, `load-to-pgstac`)? (A) Not sure of the exact names that represents tasks, but you can reference my reference to question two in [## 1. Overall Goals and Scope](#1-overall-goals-and-scope) for more details.
3. Should the PRD assume a workflow engine (e.g., Airflow, Prefect) or just plain Python scripts and CLI composition? (A) For now, let's just focus on plain Python scripts and CLI composition.

***

## 7. Performance, Scale, and Reliability

1. What are your performance expectations (e.g., “process 800K Items in under X hours” at a given hardware spec)? (A) I'm not sure of the exact performance expectations at the moment but we should parallelize the processing of items as much as possible and run asynchronous requests to API endpoints.
2. How tolerant are you of partial failures (e.g., some Items fail to ingest) vs strict all-or-nothing behavior? (A) Flag failed items and continue processing. It's to be assumed that we'll be using logging to track all the processes, and we can use the logs to identify failed items. To help the user identify failed items for review, we can add a summary at the end of the process and save the failed items to a file. As to what format and data structure of the saved failed items, that can be determined as we progress.
3. Do you have API rate limits / quotas for CMR-STAC we should design around, or should the PRD include rate-limiting and backoff as explicit requirements? (A) I'm not sure of the exact rate limits at the moment but we should include rate-limiting and backoff as explicit requirements.

***

## 8. Data Quality, Validation & Provenance

1. How strict should validation be? Should invalid items:
    - fail the whole run,
    - be logged and skipped,
    - or be quarantined for later review? (A) Flag failed items and continue processing.
2. Do you need lineage metadata (e.g., “derived from CMR concept-id X at time T using version V of this tool”) stored on Collections/Items? (A) We can use `updated` from the [common metadata](https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#date-and-time) fields. All timestamps MUST be formatted according to [RFC 3339, section 5.6](https://tools.ietf.org/html/rfc3339#section-5.6).
3. Are there external validation tools/standards you must integrate with (e.g., `stac-validator`, custom JSON Schemas, internal QA rules)? (A) No, we can use `stac-validator` for now.

***

## 9. Configuration, Environments & Deployment

1. In what environments will this run (local dev machine, on-prem server, Kubernetes, cloud batch jobs, etc.)? (A) Local system. We can use Docker to containerize workflow tasks as custom python scripts, using the tool as a library.
2. How do you want configuration handled (YAML/JSON config files, environment variables, command-line flags, all of the above)? (A) YAML/JSON config files. We can use environment variables for sensitive information.
3. Are there specific Python versions and dependency constraints (e.g., must support Python 3.10+, avoid heavy dependencies, etc.)? (A) Python 3.12+. We can use `pyproject.toml` to manage dependencies.

***

## 10. Security, Access, and Governance

1. Will CMR-STAC access require credentials/tokens in your setup, and do you have requirements for secret management (e.g., environment vars vs vault)? (A) I don't believe credentials/tokens are required for access to CMR-STAC endpoints.
2. Do you need access controls or redaction logic on the resulting Items (e.g., restricting certain metadata or assets to specific users/systems)? (A) No, that is not required.
3. Are there any licensing/compliance requirements (NASA-1.3, internal policies) that should influence how the tool and resulting catalogs are distributed? (A) No, I can't think of any at the moment.

***

## 11. Developer Experience & Coding Agent Integration

1. How do you plan to use a coding agent with the spec (e.g., generate new tools, modify existing workflows, write tests)? (A) I plan to use a coding agent with the spec to generate new tools, modify existing workflows, build new modules, and write tests.
2. What level of detail do you want in the PRD: high-level capabilities and constraints, or very fine-grained requirements (input/output schemas, error codes, etc.)? (A) High-level capabilities and constraints.
3. Do you prefer a test-first framing in the spec (e.g., scenario-based acceptance tests) to drive the coding agent? (A) Idealy, yes but not required.

***

## 12. Roadmap & Prioritization

1. Which capabilities must exist in v1 for the project to be useful, and which can be postponed to later phases? (A) All capabilities must exist in v1 for the project to be useful.
2. Are there external deadlines or milestones (e.g., a conference demo, integration with another system) that influence scope or sequencing? (A) No, main goal is to have a working prototype. A specific miltestone to shoot for is to update the existing [EasierData STAC Catalog](https://stac.easierdata.info) with new extension metadata fields. We could clone that catalog and update the clone with new extension metadata fields, update the metadata, remove metadata fields that are no longer needed, and save the updated metadata catalog as a JSON file.

***
