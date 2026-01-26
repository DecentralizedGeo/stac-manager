"""Command-line interface for STAC Manager."""
import click
import sys
import asyncio
import logging
from pathlib import Path
from stac_manager import __version__, StacManager
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


@cli.command('run-workflow')
@click.argument('config_file', type=click.Path(exists=True))
@click.option(
    '--checkpoint-dir',
    type=click.Path(),
    default='./checkpoints',
    help='Directory for checkpoint storage (default: ./checkpoints)'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Validate configuration without executing pipeline'
)
@click.pass_context
def run_workflow(ctx, config_file, checkpoint_dir, dry_run):
    """
    Execute a STAC Manager workflow from YAML configuration.
    
    Arguments:
        config_file: Path to workflow YAML file
    """
    log_level = ctx.obj.get('log_level', 'INFO')
    
    try:
        # Load workflow
        click.echo(f"Loading workflow: {config_file}")
        workflow = load_workflow_from_yaml(Path(config_file))
        
        if dry_run:
            # Validate only
            click.echo(click.style("\n[DRY RUN MODE]", fg='yellow'))
            click.echo(f"Would execute workflow: {workflow.name}")
            click.echo(f"Steps: {len(workflow.steps)}")
            
            execution_order = build_execution_order(workflow.steps)
            click.echo(f"Execution order: {' → '.join(execution_order)}")
            
            if workflow.strategy.matrix:
                click.echo(f"Matrix entries: {len(workflow.strategy.matrix)}")
            
            click.echo(click.style("\n✓ Configuration is valid", fg='green'))
            sys.exit(0)
        
        # Execute workflow
        click.echo(f"\nExecuting workflow: {workflow.name}")
        
        manager = StacManager(
            config=workflow,
            checkpoint_dir=Path(checkpoint_dir),
            log_level=log_level
        )
        
        # Run async execution
        result = asyncio.run(manager.execute())
        
        # Handle results (single or matrix)
        if isinstance(result, list):
            # Matrix strategy results
            click.echo(f"\n{'='*60}")
            click.echo("MATRIX STRATEGY RESULTS")
            click.echo(f"{'='*60}")
            
            for i, r in enumerate(result, 1):
                status_color = 'green' if r.success else 'red'
                click.echo(f"\nPipeline {i}: ", nl=False)
                click.echo(click.style(r.status, fg=status_color))
                click.echo(f"  Items processed: {r.total_items_processed}")
                click.echo(f"  Failures: {r.failure_count}")
            
            # Overall summary
            successful = sum(1 for r in result if r.success)
            total_items = sum(r.total_items_processed for r in result)
            total_failures = sum(r.failure_count for r in result)
            
            click.echo(f"\n{'='*60}")
            click.echo(f"Overall: {successful}/{len(result)} pipelines succeeded")
            click.echo(f"Total items: {total_items}")
            click.echo(f"Total failures: {total_failures}")
            
            sys.exit(0 if successful == len(result) else 1)
        else:
            # Single pipeline result
            click.echo(f"\n{'='*60}")
            click.echo("WORKFLOW RESULTS")
            click.echo(f"{'='*60}")
            
            status_color = 'green' if result.success else 'red'
            click.echo("Status: ", nl=False)
            click.echo(click.style(result.status, fg=status_color))
            click.echo(f"Items processed: {result.total_items_processed}")
            click.echo(f"Failures: {result.failure_count}")
            
            sys.exit(0 if result.success else 1)
            
    except ConfigurationError as e:
        click.echo(click.style(f"✗ Configuration error: {e}", fg='red'), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"✗ Execution failed: {e}", fg='red'), err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()

