import asyncio
import logging
import os
import sys

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from stac_manager.manager import StacManager
from stac_manager.config import WorkflowDefinition, StepConfig, SettingsConfig

async def main():
    # Define the workflow programmatically using Pydantic models
    # This mirrors the YAML structure but shows how to use the SDK directly.
    
    workflow = WorkflowDefinition(
        name="sdk-example-pipeline",
        description="Run a full pipeline using the Python SDK",
        settings=SettingsConfig(logging={"level": "INFO"}),
        steps=[
            # Step 1: Discovery
            StepConfig(
                id="discover",
                module="DiscoveryModule",
                config={
                    "catalog_url": "https://stac.easierdata.info/",
                    "collection_ids": ["HLSS30_2.0"]
                }
            ),
            # Step 2: Ingest
            StepConfig(
                id="ingest",
                module="IngestModule",
                depends_on=["discover"],
                config={
                    "collection_id": "HLSS30_2.0",
                    "limit": 3
                }
            ),
            # Step 3: Transform
            StepConfig(
                id="transform",
                module="TransformModule",
                depends_on=["ingest"],
                config={
                    "strategy": "merge",
                    "mappings": [
                        {
                            "source_field": "id", 
                            "target_field": "properties.python_processed", 
                            "type": "string"
                        }
                    ]
                }
            ),
             # Step 4: Validate
            StepConfig(
                id="validate",
                module="ValidateModule",
                depends_on=["transform"],
                config={"strict": False}
            ),
             # Step 5: Output
            StepConfig(
                id="output",
                module="OutputModule",
                depends_on=["validate"],
                config={
                    "format": "json",
                    "output_path": "data/output/sdk_run",
                    "organize_by": "flat"
                }
            )
        ]
    )
    
    print(f"Initializing Manager for Workflow: {workflow.name}")
    manager = StacManager(workflow)
    
    print("Executing...")
    result = await manager.execute()
    
    print(f"Execution Completed: {result}")
    
    # Verify output
    out_dir = "data/output/sdk_run"
    if os.path.exists(out_dir):
        files = os.listdir(out_dir)
        json_files = [f for f in files if f.endswith(".json")]
        print(f"Generated {len(json_files)} output files in {out_dir}")
    else:
        print(f"Output directory {out_dir} not found!")

if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
