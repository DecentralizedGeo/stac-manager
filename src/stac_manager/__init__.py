"""
STAC Manager - Build, orchestrate, and execute modular STAC data pipelines.

Example programmatic usage:

    from stac_manager import StacManager
    
    config = {
        "name": "my-workflow",
        "steps": [
            {"id": "ingest", "module": "IngestModule", "config": {...}},
            {"id": "output", "module": "OutputModule", "config": {...}}
        ]
    }
    
    manager = StacManager(config=config)
    result = await manager.execute()

Example YAML usage:

    from stac_manager import load_workflow_from_yaml, StacManager
    
    workflow = load_workflow_from_yaml(Path("workflow.yaml"))
    manager = StacManager(config=workflow)
    result = await manager.execute()
"""

from stac_manager.core import (
    StacManager,
    WorkflowResult,
    load_workflow_from_yaml,
    WorkflowDefinition,
    StepConfig,
    StrategyConfig,
)

__version__ = "1.0.0"

__all__ = [
    'StacManager',
    'WorkflowResult',
    'load_workflow_from_yaml',
    'WorkflowDefinition',
    'StepConfig',
    'StrategyConfig',
]
