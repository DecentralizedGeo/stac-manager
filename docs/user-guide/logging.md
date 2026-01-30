# logging System Guide

STAC Manager provides a comprehensive, structured logging system designed to give you visibility into your data pipelines while keeping noise under control.

## Overview

The logging system is built around three key principles:
1. **Structured Format**: Pipe-separated messages (`Operation | key: value`) for easy parsing.
2. **Hierarchical Control**: Configure logging globally or for specific pipeline steps.
3. **Operational Focus**: Clear separation between high-level status (INFO) and diagnostic details (DEBUG).

## Configuration

You can control logging levels in your workflow YAML configuration.

### Global Configuration
Set the default log level and advanced options for the entire workflow in `settings`:

```yaml
name: my-workflow
settings:
  logging:
    level: INFO  # Options: DEBUG, INFO, WARNING, ERROR (Default: INFO)
    output_format: text  # Options: text, json (Default: text)
    progress_interval: 100  # Log "Processed N items" every N items (Default: 100)
    
    # Log Rotation Settings
    file: logs/stac_manager.log
    file_size: 10         # Size in MB (Default: 10)
    backup_count: 5       # Keep 5 backup files (Default)
steps:
  ...
```

### Per-Step Overrides
Need to debug a specific problematic step? Override the level just for that module:

```yaml
steps:
  - id: ingest-landsat
    module: IngestModule
    config:
      mode: api
      source: microsoft/planetary-computer
    log_level: INFO
    
  - id: complex-transform
    module: TransformModule
    config: ...
    log_level: DEBUG  # Enable detailed logging only for this step
```

## Log Levels

| Level | Purpose | What You Will See |
|-------|---------|-------------------|
| **INFO** | **Operations** | High-level summaries, item counts, start/stop events. <br> *Use for normal production runs.* |
| **DEBUG**| **Diagnostics**| Detailed per-item processing, individual field changes, cache hits/misses. <br> *Use when troubleshooting data issues.* |
| **WARNING**| **Alerts** | Recoverable issues (e.g., validation failures in permissive mode). |
| **ERROR** | **Failures** | Critical errors that stop the pipeline (tier 1 failures). |

## Reading Logs

Logs follow a consistent pipe-separated format:
`[Timestamp] [Level] [Module] Operation | key: value | key: value`

### Examples

**Ingest (INFO)**
```
INFO [ingest] Starting ingest | mode: api | source: microsoft/planetary-computer
INFO [ingest] Ingest complete | total_items: 1540 | duration: 45s
```

**Extension Application (INFO vs DEBUG)**
```
# INFO: Summary
INFO [modify] Applied extension | item: LC09... | fields_scaffolded: 12 | defaults_applied: 3

# DEBUG: Details
DEBUG [modify] Processing item | item: LC09...
DEBUG [modify] Added extension URI | item: LC09... | uri: https://stac-extensions.github.io/projection/v1.1.0/schema.json
DEBUG [modify] Scaffolded properties | item: LC09... | fields: 5
```

**Output (INFO)**
```
INFO [output] Auto-flush triggered | buffered: 100 | total_written: 500
INFO [output] Flushed to disk | format: json | items: 100
```

## Troubleshooting

### "I'm seeing too many logs"
- Ensure your global level is set to `INFO` (not `DEBUG`).
- Check if any specific steps have `log_level: DEBUG` overriding the global setting.

### "I need to see why a field isn't updating"
- Set the `UpdateModule` or `TransformModule` step to `log_level: DEBUG`.
- Look for `Applied update` or `Mapped field` messages for specific items.

### "Where are the error details?"
- Validation failures are logged as WARNINGS in permissive mode.
- Critical configuration errors appear as ERRORS and will stop the workflow.
- Check the `failure_collector` summary at the end of the run for item-level failures.
