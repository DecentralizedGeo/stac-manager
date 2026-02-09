"""CLI integration tests."""
import json
from pathlib import Path
from click.testing import CliRunner
from stac_manager.cli import cli


def test_cli_run_workflow_full_pipeline():
    """Test CLI run-workflow command with full pipeline."""
    runner = CliRunner()
    
    with runner.isolated_filesystem():
        # Create test data
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
        
        with open('items.json', 'w') as f:
            json.dump(test_items, f)
        
        # Create workflow config
        with open('workflow.yaml', 'w') as f:
            f.write("""
name: cli-integration-test
steps:
  - id: ingest
    module: IngestModule
    config:
      mode: file
      source: items.json
      format: json
  - id: update
    module: UpdateModule
    config:
      fields:
        properties.cli_test: true
    depends_on: [ingest]
  - id: output
    module: OutputModule
    config:
      base_dir: ./output
      format: json
    depends_on: [update]
""")
        
        # Run via CLI
        result = runner.invoke(cli, ['run-workflow', 'workflow.yaml'])
        
        # Verify success
        assert result.exit_code == 0
        assert Path('./output').exists()


def test_cli_validate_then_run():
    """Test CLI workflow: validate then run."""
    runner = CliRunner()
    
    with runner.isolated_filesystem():
        test_items = [
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
        ]
        
        with open('items.json', 'w') as f:
            json.dump(test_items, f)
        
        with open('workflow.yaml', 'w') as f:
            f.write("""
name: validate-then-run-test
steps:
  - id: ingest
    module: IngestModule
    config:
      mode: file
      source: items.json
      format: json
  - id: output
    module: OutputModule
    config:
      base_dir: ./output
      format: json
    depends_on: [ingest]
""")
        
        # Validate first
        validate_result = runner.invoke(cli, ['validate-workflow', 'workflow.yaml'])
        assert validate_result.exit_code == 0
        assert 'valid' in validate_result.output.lower()
        
        # Then run
        run_result = runner.invoke(cli, ['run-workflow', 'workflow.yaml'])
        assert run_result.exit_code == 0
