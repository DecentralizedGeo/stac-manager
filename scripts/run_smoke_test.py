import asyncio
import logging
import os
import sys

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from stac_manager.cli import run

async def main():
    # Helper to run CLI command programmatically
    # We could call StacManager directly, but checking CLI entry point covers more ground.
    
    config_path = "examples/smoke-test.yaml"
    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found")
        sys.exit(1)
        
    print(f"Running smoke test with {config_path}...")
    
    # We'll use os.system for simplicity to run the full CLI command, 
    # OR we can just use the click context if we want to stay in python.
    # But let's verify via the actual shell entry point wrapper logic or just call check_call/run.
    
    import subprocess
    cmd = ["poetry", "run", "python", "src/stac_manager/cli.py", "run", config_path]
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd, shell=True if os.name == 'nt' else False)
        print("Smoke test successfully executed.")
    except subprocess.CalledProcessError as e:
        print(f"Smoke test failed with return code {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    asyncio.run(main())
