import click
import asyncio
import yaml
import sys
from stac_manager.config import WorkflowDefinition
from stac_manager.manager import StacManager
from stac_manager.log_utils import setup_logger, LogRunContext
from stac_manager.utils import substitute_env_vars, validate_workflow_config, generate_processing_summary

@click.group()
def main():
    """STAC Manager CLI"""
    pass

@main.command()
@click.argument('config_path', type=click.Path(exists=True))
def run(config_path):
    """Run a workflow defined in a YAML configuration file."""
    with open(config_path) as f:
        raw_config = yaml.safe_load(f)
        
    # 1. Substitute Environment Variables
    try:
        config = substitute_env_vars(raw_config)
    except Exception as e:
        click.echo(f"Configuration Error: {e}", err=True)
        sys.exit(1)

    # 2. Validate Configuration
    errors = validate_workflow_config(config)
    if errors:
        click.echo("Workflow Configuration Validation Failed:", err=True)
        for err in errors:
            click.echo(f"- {err}", err=True)
        sys.exit(1)
        
    # 3. Setup Logging
    setup_logger(config)
    
    wf_def = WorkflowDefinition(**config)
    manager = StacManager(wf_def)
    
    click.echo(f"Starting workflow: {wf_def.name}")
    
    # Wrap execution with header/footer logging
    with LogRunContext(manager.context.logger, wf_def.name, config_path):
        result = asyncio.run(manager.execute())
    
    # 5. Generate Summary
    try:
        summary = generate_processing_summary(result, manager.failure_collector)
        click.echo(summary)
    except Exception as e:
        click.echo(f"Error generating summary: {e}", err=True)
        click.echo(f"Workflow finished: {result}")

    if result.get('failure_count', 0) > 0:
        pass # Optional exit handling

if __name__ == '__main__':
    main()
