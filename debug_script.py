
import asyncio
from pathlib import Path
from stac_manager import StacManager, load_workflow_from_yaml

async def main():
    config_path = Path("examples/landsat-dgeo-migration.yaml")
    print(f"Loading {config_path}...")
    workflow = load_workflow_from_yaml(config_path)
    
    manager = StacManager(config=workflow)
    print("Executing workflow...")
    result = await manager.execute()
    
    # Handle list result (matrix) or single result
    results = result if isinstance(result, list) else [result]
    
    for i, res in enumerate(results):
        print(f"\n--- Result {i} ---")
        print(f"Status: {res.status}")
        print(f"Failures: {res.failure_count}")
        
        if res.failure_collector:
            print("Failure Details:")
            for fail in res.failure_collector.get_all():
                print(f"  Item: {fail.item_id}, Step: {fail.step_id}, Type: {fail.error_type}, Error: {fail.message}")


if __name__ == "__main__":
    asyncio.run(main())
