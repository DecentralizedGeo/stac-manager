"""Command-line interface for STAC Manager."""
import click
from stac_manager import __version__


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


if __name__ == '__main__':
    cli()
