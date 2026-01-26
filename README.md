# STAC Manager

**Modular Pipeline Orchestration for STAC Catalogs**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## What is STAC Manager?

STAC Manager is a Python library for building, orchestrating, and executing modular STAC data pipelines. It enables you to ingest STAC items from APIs or files, transform and enrich metadata, validate compliance, apply extensions, and output to various formats—all through declarative YAML configuration or a programmatic Python API.

Built on the **Pipes and Filters** architecture, STAC Manager provides 7 specialized modules that compose into powerful workflows while maintaining simplicity and testability.

---

## Key Features

- 🔌 **Modular Architecture**: 7 pipeline modules (Ingest, Seed, Transform, Update, Validate, Extension, Output)
- 📝 **Declarative Configuration**: Define workflows in YAML with full validation
- 🔄 **Streaming Pipeline**: Process millions of items with constant memory usage
- ✅ **STAC Compliance**: Built-in validation using `stac-validator`
- 🎯 **Matrix Strategies**: Run parallel pipelines for multiple collections
- 💾 **Checkpoint Resume**: Recover from failures without re-processing completed items
- 🐍 **Python 3.12+**: Modern type hints and structural pattern matching

---

## Quick Example

```yaml
# workflow.yaml
name: ingest-and-validate
steps:
  - id: fetch
    module: IngestModule
    config:
      mode: api
      url: https://planetarycomputer.microsoft.com/api/stac/v1
      collections: [sentinel-2-l2a]
      max_items: 100

  - id: validate
    module: ValidateModule
    depends_on: [fetch]
    config:
      strict: true

  - id: output
    module: OutputModule
    depends_on: [validate]
    config:
      base_dir: ./outputs
      format: json
```

Run it:

```bash
stac-manager run-workflow workflow.yaml
```

---

## Installation

**Requirements**: Python 3.12+

### Via pip (recommended)

```bash
pip install stac-manager
```

### Via Poetry

```bash
poetry add stac-manager
```

### From Source

```bash
git clone https://github.com/DecentralizedGeo/stac-manager.git
cd stac-manager
poetry install
```

Verify installation:

```bash
stac-manager --version
```

---

## Next Steps

- 📖 **[Installation Guide](docs/user-guide/installation.md)** - Detailed setup instructions
- 🚀 **[Quickstart](docs/user-guide/quickstart.md)** - Run your first workflow in 5 minutes
- 📚 **[Tutorials](docs/user-guide/tutorials/)** - Progressive examples from basic to advanced
- 🔧 **[Module Reference](docs/spec/stac-manager-v1.0.0/)** - Complete module documentation

---

## Project Status

**Current Version**: 1.0.0 (Stable)

✅ **Implemented**:
- Phase 1: Utilities Foundation
- Phase 2: Pipeline Modules (7 modules)
- Phase 3: Orchestration Layer (CLI, Checkpoints, Matrix)
- Phase 4: End-User Documentation

📋 **Roadmap**: See [ROADMAP.md](docs/plans/2026-01-22-stac-manager-roadmap.md) for future features.

---

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

Built with:
- [PySTAC](https://pystac.readthedocs.io/) - STAC data models
- [pystac-client](https://pystac-client.readthedocs.io/) - STAC API client
- [stac-validator](https://github.com/stac-utils/stac-validator) - STAC validation
- [stac-geoparquet](https://github.com/stac-utils/stac-geoparquet) - Parquet conversion
