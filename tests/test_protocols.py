from typing import AsyncIterator, Any
from stac_manager.protocols import Fetcher, Modifier, Bundler
import pytest

class MockFetcher:
    def __init__(self, config: dict): pass
    async def fetch(self, context) -> AsyncIterator[dict]:
        yield {}

def test_fetcher_protocol():
    assert isinstance(MockFetcher({}), Fetcher)
