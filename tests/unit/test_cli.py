"""Tests for CLI interface."""
from click.testing import CliRunner
from pathlib import Path
import tempfile
import json
from stac_manager.cli import cli


def test_cli_main_help():
    """Test CLI shows help message."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])

    assert result.exit_code == 0
    assert 'stac-manager' in result.output.lower()
    assert 'run-workflow' in result.output.lower()
    assert 'validate-workflow' in result.output.lower()


def test_cli_version():
    """Test CLI shows version."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])

    assert result.exit_code == 0
    assert '1.0.0' in result.output  # Should match package version


def test_validate_workflow_valid_config():
    """Test validate-workflow accepts valid configuration."""
    runner = CliRunner()

    # Create valid workflow file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
name: test-workflow
steps:
  - id: ingest
    module: IngestModule
    config:
      source_file: test.json
""")
        yaml_path = f.name

    try:
        result = runner.invoke(cli, ['validate-workflow', yaml_path])

        assert result.exit_code == 0
        assert 'valid' in result.output.lower() or 'success' in result.output.lower()
    finally:
        Path(yaml_path).unlink()


def test_validate_workflow_invalid_config():
    """Test validate-workflow detects invalid configuration."""
    runner = CliRunner()

    # Create invalid workflow file (missing required fields)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
name: test-workflow
steps:
  - id: ingest
    # Missing 'module' field
    config: {}
""")
        yaml_path = f.name

    try:
        result = runner.invoke(cli, ['validate-workflow', yaml_path])

        assert result.exit_code != 0
        assert 'error' in result.output.lower() or 'invalid' in result.output.lower()
    finally:
        Path(yaml_path).unlink()


def test_validate_workflow_detects_cycle():
    """Test validate-workflow detects circular dependencies."""
    runner = CliRunner()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
name: cycle-workflow
steps:
  - id: step_a
    module: UpdateModule
    config: {}
    depends_on: [step_b]
  - id: step_b
    module: TransformModule
    config: {}
    depends_on: [step_a]
""")
        yaml_path = f.name

    try:
        result = runner.invoke(cli, ['validate-workflow', yaml_path])

        assert result.exit_code != 0
        assert 'circular' in result.output.lower() or 'cycle' in result.output.lower()
    finally:
        Path(yaml_path).unlink()


def test_validate_workflow_file_not_found():
    """Test validate-workflow handles missing file."""
    runner = CliRunner()
    result = runner.invoke(cli, ['validate-workflow', '/nonexistent/file.yaml'])

    assert result.exit_code != 0
    assert ('not found' in result.output.lower() or 'does not exist' in result.output.lower())


def test_run_workflow_basic():
    """Test run-workflow executes a simple workflow."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create test data
        test_items = [
            {
                "type": "Feature",
                "stac_version": "1.0.0",
                "id": "test-item-1",
                "geometry": {"type": "Point", "coordinates": [0, 0]},
                "bbox": [0, 0, 0, 0],
                "properties": {"datetime": "2024-01-01T00:00:00Z"},
                "links": [],
                "assets": {}
            }
        ]

        with open('test_items.json', 'w') as f:
            json.dump(test_items, f)

        # Create workflow config
        with open('workflow.yaml', 'w') as f:
            f.write("""
name: test-workflow
steps:
  - id: ingest
    module: IngestModule
    config:
      mode: file
      source: test_items.json
      format: json
  - id: output
    module: OutputModule
    config:
      base_dir: ./output
      format: json
    depends_on: [ingest]
""")

        # Run workflow
        result = runner.invoke(cli, ['run-workflow', 'workflow.yaml'])

        # Should complete successfully
        assert result.exit_code == 0
        assert 'completed' in result.output.lower() or 'success' in result.output.lower()


def test_run_workflow_dry_run():
    """Test run-workflow --dry-run validates without executing."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        with open('workflow.yaml', 'w') as f:
            f.write("""
name: dry-run-test
steps:
  - id: seed
    module: SeedModule
    config:
      items: []
""")

        result = runner.invoke(cli, ['run-workflow', '--dry-run', 'workflow.yaml'])

        assert result.exit_code == 0
        assert 'dry' in result.output.lower() or 'would execute' in result.output.lower()


def test_run_workflow_with_checkpoint_dir():
    """Test run-workflow with custom checkpoint directory."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        test_items = [
            {
                "type": "Feature",
                "stac_version": "1.0.0",
                "id": "test-item-1",
                "geometry": {"type": "Point", "coordinates": [0, 0]},
                "bbox": [0, 0, 0, 0],
                "properties": {"datetime": "2024-01-01T00:00:00Z"},
                "links": [],
                "assets": {}
            }
        ]

        with open('test_items.json', 'w') as f:
            json.dump(test_items, f)

        with open('workflow.yaml', 'w') as f:
            f.write("""
name: checkpoint-test
steps:
  - id: ingest
    module: IngestModule
    config:
      mode: file
      source: test_items.json
      format: json
  - id: output
    module: OutputModule
    config:
      base_dir: ./output
      format: json
    depends_on: [ingest]
""")

        result = runner.invoke(cli, [
            'run-workflow',
            '--checkpoint-dir', './custom_checkpoints',
            'workflow.yaml'
        ])

        assert result.exit_code == 0
        assert Path('./custom_checkpoints').exists()


def test_run_workflow_shows_progress():
    """Test run-workflow shows progress messages."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        test_items = [
            {
                "type": "Feature",
                "stac_version": "1.0.0",
                "id": f"item-{i}",
                "geometry": {"type": "Point", "coordinates": [0, 0]},
                "bbox": [0, 0, 0, 0],
                "properties": {"datetime": "2024-01-01T00:00:00Z"},
                "links": [],
                "assets": {}
            }
            for i in range(5)
        ]

        with open('test_items.json', 'w') as f:
            json.dump(test_items, f)

        with open('workflow.yaml', 'w') as f:
            f.write("""
name: progress-test
steps:
  - id: ingest
    module: IngestModule
    config:
      mode: file
      source: test_items.json
      format: json
  - id: output
    module: OutputModule
    config:
      base_dir: ./output
      format: json
    depends_on: [ingest]
""")

        result = runner.invoke(cli, ['run-workflow', 'workflow.yaml'])

        # Should show progress messages
        assert 'loading' in result.output.lower() or 'executing' in result.output.lower()
        assert 'ingest' in result.output.lower() or 'progress-test' in result.output.lower()


def test_run_workflow_verbose_logging():
    """Test run-workflow with --log-level DEBUG shows detailed output."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        with open('test_items.json', 'w') as f:
            json.dump([
                {
                    "type": "Feature",
                    "stac_version": "1.0.0",
                    "id": "test-item",
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                    "bbox": [0, 0, 0, 0],
                    "properties": {"datetime": "2024-01-01T00:00:00Z"},
                    "links": [],
                    "assets": {}
                }
            ], f)

        with open('workflow.yaml', 'w') as f:
            f.write("""
name: verbose-test
steps:
  - id: ingest
    module: IngestModule
    config:
      mode: file
      source: test_items.json
      format: json
  - id: output
    module: OutputModule
    config:
      base_dir: ./output
      format: json
    depends_on: [ingest]
""")

        result = runner.invoke(cli, ['--log-level', 'DEBUG', 'run-workflow', 'workflow.yaml'])

        # Should show more detailed output with DEBUG level
        assert result.exit_code == 0

