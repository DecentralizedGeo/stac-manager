import requests
import json
import os
from pathlib import Path
from typing import Any, Dict

FIXTURES_DATA_DIR = Path(__file__).parent / "data"

def download_fixture(url: str, filename: str) -> Dict[str, Any]:
    """
    Download a JSON fixture if it doesn't exist locally.
    
    Args:
        url: URL to download from
        filename: Local filename to save as
        
    Returns:
        JSON content as dict
    """
    FIXTURES_DATA_DIR.mkdir(exist_ok=True, parents=True)
    local_path = FIXTURES_DATA_DIR / filename
    
    if local_path.exists():
        with open(local_path, "r") as f:
            return json.load(f)
            
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        with open(local_path, "w") as f:
            json.dump(data, f, indent=2)
            
        return data
    except Exception as e:
        print(f"Failed to download fixture from {url}: {e}")
        return {}
