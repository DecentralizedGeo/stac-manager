"""Tests for CLI interface."""
from click.testing import CliRunner
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
