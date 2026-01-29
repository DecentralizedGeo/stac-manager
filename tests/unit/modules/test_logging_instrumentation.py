import pytest
import logging
from unittest.mock import MagicMock, AsyncMock, patch
from stac_manager.modules.ingest import IngestModule
from stac_manager.modules.seed import SeedModule
from tests.fixtures.context import MockWorkflowContext

@pytest.mark.asyncio
async def test_ingest_module_logs_events():
    """Test that IngestModule logs key events."""
    # Mock logger
    mock_logger = MagicMock(spec=logging.Logger)
    
    # Setup context with mock logger
    context = MockWorkflowContext.create()
    context.logger = mock_logger
    
    # Setup IngestModule
    config = {
        "mode": "file",
        "source": "items.json",
        "format": "json"
    }
    
    # Mock file reading to avoid actual IO
    with patch('stac_manager.modules.ingest.IngestModule._fetch_from_file') as mock_fetch:
        async def async_gen():
            yield {"id": "item-1"}
        mock_fetch.side_effect = async_gen
        
        # Patch Path.exists to skip validation
        with patch('pathlib.Path.exists', return_value=True):
            module = IngestModule(config)
            
            # Run fetch
            _ = [item async for item in module.fetch(context)]
        
        # Verify Logs
        # We expect at least an INFO log about starting/fetching
        assert mock_logger.info.called or mock_logger.debug.called

@pytest.mark.asyncio
async def test_ingest_module_logs_item_details():
    """Test that IngestModule logs item details at DEBUG level."""
    mock_logger = MagicMock(spec=logging.Logger)
    context = MockWorkflowContext.create()
    context.logger = mock_logger
    
    config = {
        "mode": "file",
        "source": "items.json"
    }
     # Mock iter
    with patch('stac_manager.modules.ingest.IngestModule._load_json_file') as mock_load:
        # Assume it yields one item
        async def async_gen(_):
            yield {"id": "test-item"}
        mock_load.side_effect = async_gen
        
        # We also need _determine_source_type to work
        with patch('stac_manager.modules.ingest.IngestModule._determine_source_type', return_value="file"):
            with patch('pathlib.Path.exists', return_value=True):
                module = IngestModule(config)
                
                # Execute
                [i async for i in module.fetch(context)]
                
                # Verify DEBUG log for item
                # Expecting: logger.debug("Fetched item test-item ...")
                debug_calls = [args[0] for args, _ in mock_logger.debug.call_args_list]
                assert any("test-item" in str(call) for call in debug_calls)

@pytest.mark.asyncio
async def test_seed_module_logs_generation():
    """Test that SeedModule logs generated items."""
    mock_logger = MagicMock(spec=logging.Logger)
    context = MockWorkflowContext.create()
    context.logger = mock_logger
    
    config = {
        "items": [{"id": "seed-item", "type": "Feature"}]
    }
    
    module = SeedModule(config)
    
    [i async for i in module.fetch(context)]
    
    # Verify DEBUG log
    debug_calls = [args[0] for args, _ in mock_logger.debug.call_args_list]
    assert any("seed-item" in str(call) for call in debug_calls)

@pytest.mark.asyncio
async def test_update_module_logs_operations():
    """Test that UpdateModule logs modification details."""
    mock_logger = MagicMock(spec=logging.Logger)
    context = MockWorkflowContext.create()
    context.logger = mock_logger
    
    config = {
        "updates": {"properties.updated": True}
    }
    
    from stac_manager.modules.update import UpdateModule
    module = UpdateModule(config)
    
    # Process item
    item = {"id": "test-item", "properties": {}}
    module.modify(item, context)
    
    # Verify logs
    # Expecting DEBUG log about modification
    debug_calls = [args[0] for args, _ in mock_logger.debug.call_args_list]
    assert any("test-item" in str(call) for call in debug_calls)
    assert any("fields" in str(call) or "updated" in str(call) for call in debug_calls)

@pytest.mark.asyncio
async def test_transform_module_logs_enrichment():
    """Test that TransformModule logs enrichment details."""
    mock_logger = MagicMock(spec=logging.Logger)
    context = MockWorkflowContext.create()
    context.logger = mock_logger
    
    config = {
        "input_file": "sidecar.csv", # Mocked
        "input_join_key": "id",
        "field_mapping": {"properties.enrich": "data_column"}
    }
    
    from stac_manager.modules.transform import TransformModule
    
    with patch('stac_manager.modules.transform.TransformModule._load_csv') as mock_load:
        
        with patch('pathlib.Path.exists', return_value=True):
            module = TransformModule(config)
            # Manually set index after init
            module.sidecar_index = {"test-item": {"data_column": "enriched"}}
            
            # Process item
            item = {"id": "test-item", "properties": {}}
            module.modify(item, context)
            
            # Verify logs
            # Expecting DEBUG log about enrichment
            debug_calls = [args[0] for args, _ in mock_logger.debug.call_args_list]
            assert any("test-item" in str(call) for call in debug_calls)
            assert any("enriched" in str(call) or "sidecar" in str(call) for call in debug_calls)

@pytest.mark.asyncio
async def test_output_module_logs_writes(tmp_path):
    """Test that OutputModule logs file writing."""
    mock_logger = MagicMock(spec=logging.Logger)
    context = MockWorkflowContext.create()
    context.logger = mock_logger
    
    config = {
        "base_dir": str(tmp_path),
        "format": "json",
        "buffer_size": 1
    }
    
    from stac_manager.modules.output import OutputModule
    module = OutputModule(config)
    
    # Process item
    item = {"id": "test-item", "properties": {}}
    
    # Mock file writing to avoid IO and focus on log
    # We mock os.replace and Path.mkdir too to avoid errors
    with patch('pathlib.Path.write_text') as mock_write, \
         patch('os.replace') as mock_replace, \
         patch('pathlib.Path.mkdir'):
        
        await module.bundle(item, context)
        await module.finalize(context)
        
        # Verify logs
        # Expecting DEBUG log about writing file
        debug_calls = [args[0] for args, _ in mock_logger.debug.call_args_list]
        assert any("test-item" in str(call) for call in debug_calls)
