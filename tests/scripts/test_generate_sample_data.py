"""Tests for sample data generator script."""
import pytest
from pathlib import Path
from click.testing import CliRunner
from scripts.generate_sample_data import cli


def test_cli_help():
    """Test CLI help flag displays usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    
    assert result.exit_code == 0
    assert 'generate-sample-data' in result.output.lower()
    assert '--collection' in result.output
    assert '--items' in result.output


def test_cli_requires_collection():
    """Test CLI fails without collection argument."""
    runner = CliRunner()
    result = runner.invoke(cli, [])
    
    assert result.exit_code != 0
