
import asyncio
import logging
from stac_manager.modules.discovery import DiscoveryModule
from stac_manager.modules.ingest import IngestModule
from stac_manager.context import WorkflowContext
from stac_manager.failures import FailureCollector

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_fetch")

async def run_verification():
    print("--- Starting Verification: Real Data Fetch ---")
    
    # 1. Setup Context
    ctx = WorkflowContext(
        workflow_id="manual-verify",
        config={},
        logger=logger,
        failure_collector=FailureCollector(),
        checkpoints=None,
        data={}
    )
    
    # 2. Discovery Phase
    print("\n[Phase 1] Discovery Module")
    discovery_config = {
        "catalog_url": "https://stac.easierdata.info/",
        "collection_ids": ["HLSS30_2.0"]
    }
    discovery = DiscoveryModule(discovery_config)
    
    print(f"Fetching collections from {discovery_config['catalog_url']}...")
    found_collections = []
    async for collection in discovery.fetch(ctx):
        print(f"Discovered Collection: {collection['id']}")
        found_collections.append(collection['id'])
        
    if "HLSS30_2.0" not in found_collections:
        print("WARNING: Target collection HLSS30_2.0 not found in Discovery phase. Proceeding anyway by manual injection if needed.")
    
    # Verify Context Usage
    print(f"Context 'catalog_url' set to: {ctx.data.get('catalog_url')}")
    
    # 3. Ingest Phase
    print("\n[Phase 2] Ingest Module")
    # IngestModule relies on catalog_url in context (set above)
    # It also relies on context or config for collection_id. 
    # Let's pass via config to simulate direct targeting, or inject into context.
    # The IngestModule logic: collection_id = context.data.get('_current_collection_id') or self.config.collection_id
    
    # We will simulate the orchestrator passing the current collection
    ctx.data['_current_collection_id'] = "HLSS30_2.0"
    
    ingest_config = {
        "collection_id": "HLSS30_2.0" # Backup
    }
    ingest = IngestModule(ingest_config)
    
    print(f"Fetching items from collection: HLSS30_2.0 ...")
    item_count = 0
    max_items = 100
    
    async for item in ingest.fetch(ctx):
        item_count += 1
        print(f"[{item_count}] Fetched Item: {item['id']} ({item['type']})")
        if item_count >= max_items:
            break
            
    print(f"\nVerification Complete. Fetched {item_count} items.")

if __name__ == "__main__":
    asyncio.run(run_verification())
