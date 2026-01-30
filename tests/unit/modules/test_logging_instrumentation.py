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
    
    config = {"mode": "api", "source": "https://fake.stac.api"}
    with patch('stac_manager.modules.ingest.IngestModule._fetch_from_api') as mock_fetch:
        async def async_gen(_):
            yield {"id": "test-item"}
        mock_fetch.return_value = async_gen(None)
        
        module = IngestModule(config)
        module.set_logger(mock_logger)  # Inject logger
        
        # Execute
        [i async for i in module.fetch(context)]
        
        # Verify logs
        info_calls = [args[0] for args, _ in mock_logger.info.call_args_list]
        assert len(info_calls) > 0, "Expected INFO log calls"
        assert any("Starting" in str(call) or "Ingest" in str(call) for call in info_calls)

@pytest.mark.asyncio
async def test_ingest_module_logs_item_details():
    """Test that IngestModule logs item details at DEBUG level."""
    mock_logger = MagicMock(spec=logging.Logger)
    context = MockWorkflowContext.create()
    
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
                module.set_logger(mock_logger)  # Inject logger
                
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
    
    config = {
        "updates": {"properties.updated": True}
    }
    
    from stac_manager.modules.update import UpdateModule
    module = UpdateModule(config)
    
    # Inject the mock logger (UpdateModule now uses self.logger, not context.logger)
    module.set_logger(mock_logger)
    
    # Process item
    item = {"id": "test-item", "properties": {}}
    module.modify(item, context)
    
    # Verify logs
    # Expecting DEBUG log about processing item and INFO log about applying updates
    debug_calls = [args[0] for args, _ in mock_logger.debug.call_args_list]
    info_calls = [args[0] for args, _ in mock_logger.info.call_args_list]
    
    # Check for DEBUG log with item ID
    assert any("test-item" in str(call) for call in debug_calls), \
        f"Expected 'test-item' in DEBUG logs, got: {debug_calls}"
    
    # Check for INFO log about applying updates
    assert any("Applied updates" in str(call) and "test-item" in str(call) for call in info_calls), \
        f"Expected 'Applied updates' with 'test-item' in INFO logs, got: {info_calls}"

@pytest.mark.asyncio
async def test_ingest_module_accepts_injected_logger():
    """Test IngestModule has set_logger method and uses it."""
    mock_logger = MagicMock(spec=logging.Logger)
    context = MockWorkflowContext.create()
    
    config = {"mode": "file", "source": "items.json", "format": "json"}
    
    with patch('pathlib.Path.exists', return_value=True):
        module = IngestModule(config)
        
        # Module should have set_logger method
        assert hasattr(module, 'set_logger'), "IngestModule missing set_logger method"
        
        # Inject logger
        module.set_logger(mock_logger)
        
        # Verify logger was set
        assert module.logger is mock_logger

@pytest.mark.asyncio
async def test_ingest_module_logs_info_messages():
    """Test IngestModule logs INFO-level summaries."""
    mock_logger = MagicMock(spec=logging.Logger)
    context = MockWorkflowContext.create()
    
    config = {"mode": "file", "source": "items.json", "format": "json"}
    
    with patch('stac_manager.modules.ingest.IngestModule._load_json_file') as mock_load:
        async def async_gen(_):
            yield {"id": "item-1"}
            yield {"id": "item-2"}
        mock_load.return_value = async_gen(None)
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_file', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=False):
            module = IngestModule(config)
            module.set_logger(mock_logger)
            
            # Fetch items
            items = [item async for item in module.fetch(context)]
            
            # Verify INFO logs
            info_calls = [str(args[0]) for args, _ in mock_logger.info.call_args_list]
            
            # Should log start of ingest
            assert any("Starting ingest" in call for call in info_calls), \
                f"Expected 'Starting ingest' in INFO logs, got: {info_calls}"
            
            # Should log completion with count
            assert any("Ingest complete" in call and "total_items: 2" in call for call in info_calls), \
                f"Expected 'Ingest complete | total_items: 2' in INFO logs, got: {info_calls}"

@pytest.mark.asyncio
async def test_ingest_module_logs_debug_details():
    """Test IngestModule logs DEBUG-level item details."""
    mock_logger = MagicMock(spec=logging.Logger)
    context = MockWorkflowContext.create()
    
    config = {"mode": "file", "source": "items.json", "format": "json"}
    
    with patch('stac_manager.modules.ingest.IngestModule._load_json_file') as mock_load:
        async def async_gen(_):
            yield {"id": "test-item-1", "collection": "test-collection"}
            yield {"id": "test-item-2", "collection": "test-collection"}
        mock_load.return_value = async_gen(None)
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_file', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=False):
            module = IngestModule(config)
            module.set_logger(mock_logger)
            
            items = [item async for item in module.fetch(context)]
            
            # Verify DEBUG logs
            debug_calls = [str(args[0]) for args, _ in mock_logger.debug.call_args_list]
            
            # Should log each fetched item
            assert any("test-item-1" in call for call in debug_calls), \
                f"Expected 'test-item-1' in DEBUG logs, got: {debug_calls}"
            assert any("test-item-2" in call for call in debug_calls), \
                f"Expected 'test-item-2' in DEBUG logs, got: {debug_calls}"

@pytest.mark.asyncio
async def test_transform_module_logs_enrichment():
    """Test that TransformModule logs enrichment details."""
    mock_logger = MagicMock(spec=logging.Logger)
    context = MockWorkflowContext.create()
    context.logger = mock_logger
    
    config = {
        "input_file": "sidecar.csv", # Mocked
        "input_join_key": "id",
        "field_mapping": {"properties.enrich": "data_column"},
        "strategy": "merge"  # Create new property
    }
    
    from stac_manager.modules.transform import TransformModule
    
    with patch('stac_manager.modules.transform.TransformModule._load_csv') as mock_load:
        
        with patch('pathlib.Path.exists', return_value=True):
            module = TransformModule(config)
            # Manually set index after init
            module.input_index = {"test-item": {"data_column": "enriched"}}
            
            # Process item
            item = {"id": "test-item", "properties": {}}
            module.modify(item, context)
            
            # Verify logs
            # Expecting DEBUG log about enrichment
            debug_calls = [args[0] for args, _ in mock_logger.debug.call_args_list]
            assert any("test-item" in str(call) for call in debug_calls)
            assert any("Enriching" in str(call) or "input" in str(call) for call in debug_calls)

@pytest.mark.asyncio
async def test_transform_module_accepts_injected_logger():
    """Test TransformModule has set_logger method and uses it."""
    mock_logger = MagicMock(spec=logging.Logger)
    
    config = {
        "input_file": "test.csv",
        "input_join_key": "id",
        "field_mapping": {"properties.test": "value"}
    }
    
    with patch('pathlib.Path.exists', return_value=True), \
         patch('stac_manager.modules.transform.TransformModule._load_csv'):
        from stac_manager.modules.transform import TransformModule
        module = TransformModule(config)
        
        # Module should have set_logger method
        assert hasattr(module, 'set_logger'), "TransformModule missing set_logger method"
        
        # Inject logger
        module.set_logger(mock_logger)
        
        # Verify logger was set
        assert module.logger is mock_logger

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
