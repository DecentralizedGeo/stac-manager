# CLI Interface
## STAC Manager v1.0

**Related Documents**:
- [Configuration](./03-configuration.md)

---

## 1. Overview

The CLI (`stac-manager`) provides the primary entry point for executing workflows and performing ad-hoc STAC operations. It is built using `click`.

## 2. Main Command

```bash
stac-manager [OPTIONS] COMMAND [ARGS]...
```

**Global Options**:
- `--config PATH`: Path to a base configuration file (default: `./config.yaml`).
- `--log-level [DEBUG|INFO|WARNING|ERROR]`: Override logging level.
- `--version`: Show version.

## 3. Subcommands

### `run-workflow`
Executes a full workflow defined in a YAML file.

```bash
stac-manager run-workflow --config WORKFLOW_FILE.yaml [OPTIONS]
```
- `--dry-run`: Validate DAG and config usage without executing side-effects.
- `--output-failures PATH`: Location to write the failure report (default: `./failures.json`).
- `--output-summary PATH`: Location to write the workflow execution summary (default: `./summary.json`).

### `validate-workflow`
Static analysis of a workflow configuration. Checks for valid module names, required config fields, and DAG cycles.

```bash
stac-manager validate-workflow --config WORKFLOW_FILE.yaml
```

### `discover`
Ad-hoc command wrapping the Discovery Module.

```bash
stac-manager discover --catalog-url URL [--output FILE]
```

### `validate-stac`
Run validation on local files.

```bash
stac-manager validate-stac --input ./data/items/ --recursive
```
- `--strict`: Return non-zero exit code on warnings.
- `--extensions URL`: Validate against specific extension schemas.
- `--report PATH`: Write validation report to JSON file (for CI/automated checking).

### `list-extensions`
Show available extensions in the registry.

```bash
stac-manager list-extensions
```
