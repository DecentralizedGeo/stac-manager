import click
import asyncio
import yaml
from stac_manager.config import WorkflowDefinition
from stac_manager.manager import StacManager

@click.group()
def main():
    """STAC Manager CLI"""
    pass

@main.command()
@click.argument('config_path', type=click.Path(exists=True))
def run(config_path):
    """Run a workflow defined in a YAML configuration file."""
    with open(config_path) as f:
        data = yaml.safe_load(f)
    
    wf_def = WorkflowDefinition(**data)
    manager = StacManager(wf_def)
    
    click.echo(f"Starting workflow: {wf_def.name}")
    result = asyncio.run(manager.execute())
    click.echo(f"Workflow finished: {result}")

if __name__ == '__main__':
    main()
