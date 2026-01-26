"""Tests for CLI interface."""
from click.testing import CliRunner
from pathlib import Path
import tempfile
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

