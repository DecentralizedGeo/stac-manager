"""Command-line interface for STAC Manager."""
import click
import sys
from pathlib import Path
from stac_manager import __version__
from stac_manager.core import load_workflow_from_yaml, build_execution_order
from stac_manager.exceptions import ConfigurationError


@click.group()
@click.version_option(version=__version__, prog_name='stac-manager')
@click.option(
    '--log-level',
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR'], case_sensitive=False),
    default='INFO',
    help='Set logging level'
)
@click.pass_context
def cli(ctx, log_level):
    """
    STAC Manager - Build, orchestrate, and execute modular STAC data pipelines.
    
    Examples:
    
        # Run a workflow
        stac-manager run-workflow workflow.yaml
        
        # Validate workflow configuration
        stac-manager validate-workflow workflow.yaml
    """
    ctx.ensure_object(dict)
    ctx.obj['log_level'] = log_level


@cli.command('validate-workflow')
@click.argument('config_file', type=click.Path(exists=True))
@click.pass_context
def validate_workflow(ctx, config_file):
    """
    Validate workflow configuration without executing.
    
    Checks:
    - YAML syntax and structure
    - Required fields present
    - Module names valid
    - No circular dependencies
    - Step dependencies exist
    
    Arguments:
        config_file: Path to workflow YAML file
    """
    try:
        # Load and validate configuration
        click.echo(f"Validating workflow: {config_file}")
        workflow = load_workflow_from_yaml(Path(config_file))
        
        # Validate execution order (checks for cycles)
        execution_order = build_execution_order(workflow.steps)
        
        # Success message
        click.echo(click.style("✓ Workflow configuration is valid", fg='green'))
        click.echo(f"\nWorkflow: {workflow.name}")
        click.echo(f"Steps: {len(workflow.steps)}")
        click.echo(f"Execution order: {' → '.join(execution_order)}")
        
        if workflow.strategy.matrix:
            click.echo(f"Matrix entries: {len(workflow.strategy.matrix)}")
        
        sys.exit(0)
        
    except ConfigurationError as e:
        click.echo(click.style(f"✗ Configuration error: {e}", fg='red'), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"✗ Validation failed: {e}", fg='red'), err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()

