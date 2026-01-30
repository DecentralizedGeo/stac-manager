"""Integration tests for module logging instrumentation.

Smoke tests that verify all modules properly log operations in realistic scenarios.
"""
import pytest
import logging
from unittest.mock import MagicMock, patch
from io import StringIO

from tests.fixtures.context import MockWorkflowContext


@pytest.fixture
def capture_logs():
    """Fixture to capture log messages at INFO and DEBUG levels."""
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger('test_logger')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    yield logger, log_capture
    
    logger.removeHandler(handler)


@pytest.mark.asyncio
async def test_ingest_module_logging_smoke_test(capture_logs):
    """Smoke test: IngestModule logs when fetching items."""
    logger, log_capture = capture_logs
    
    config = {
        "mode": "api",
        "source": "https://fake.stac.api"
    }
    
    from stac_manager.modules.ingest import IngestModule
    
    test_items = [
        {"id": "item-001", "type": "Feature", "properties": {}, "geometry": None},
        {"id": "item-002", "type": "Feature", "properties": {}, "geometry": None}
    ]
    
    with patch('stac_manager.modules.ingest.IngestModule._fetch_from_api') as mock_fetch:
        async def async_gen(_):
            for item in test_items:
                yield item
        
        mock_fetch.return_value = async_gen(None)
        
        module = IngestModule(config)
        module.set_logger(logger)
        
        context = MockWorkflowContext.create()
        items = [item async for item in module.fetch(context)]
    
    log_output = log_capture.getvalue()
    
    # Verify logging occurred
    assert "Starting ingest" in log_output
    assert "Ingest complete" in log_output
    assert "total_items: 2" in log_output
    assert len(items) == 2


@pytest.mark.asyncio
async def test_extension_module_logging_smoke_test(capture_logs):
    """Smoke test: ExtensionModule logs when applying extension."""
    logger, log_capture = capture_logs
    
    config = {
        "schema_uri": "https://stac-extensions.github.io/projection/v1.1.0/schema.json",
        "defaults": {
            "properties.proj:epsg": 4326
        }
    }
    
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "properties": {
                "properties": {
                    "properties": {
                        "proj:epsg": {"type": "integer"}
                    }
                }
            }
        }
        mock_get.return_value = mock_response
        
        from stac_manager.modules.extension import ExtensionModule
        module = ExtensionModule(config)
        module.set_logger(logger)
        
        context = MockWorkflowContext.create()
        item = {
            "id": "smoke-test-001",
            "type": "Feature",
            "properties": {},
            "geometry": None
        }
        
        result = module.modify(item, context)
    
    log_output = log_capture.getvalue()
    
    # Verify logging occurred
    assert "Applied extension" in log_output
    assert "smoke-test-001" in log_output
    assert "fields_scaffolded" in log_output


@pytest.mark.asyncio
async def test_output_module_logging_smoke_test(tmp_path, capture_logs):
    """Smoke test: OutputModule logs during buffering and flushing."""
    logger, log_capture = capture_logs
    
    config = {
        "base_dir": str(tmp_path),
        "format": "json",
        "buffer_size": 2  # Trigger auto-flush
    }
    
    from stac_manager.modules.output import OutputModule
    module = OutputModule(config)
    module.set_logger(logger)
    
    context = MockWorkflowContext.create()
    
    # Add items to trigger auto-flush
    for i in range(3):
        item = {
            "id": f"smoke-{i:03d}",
            "type": "Feature",
            "collection": "smoke-test",
            "properties": {},
            "geometry": None
        }
        await module.bundle(item, context)
    
    await module.finalize(context)
    
    log_output = log_capture.getvalue()
    
    # Verify logging occurred
    assert "Initialized output" in log_output
    assert "smoke-test" in log_output
    assert "Buffered item" in log_output
    assert "Flushed to disk" in log_output


@pytest.mark.asyncio
async def test_all_modules_use_injected_logger():
    """Verify all 6 modules accept and use injected loggers via set_logger()."""
    mock_logger = MagicMock(spec=logging.Logger)
    
    from stac_manager.modules.ingest import IngestModule
    from stac_manager.modules.extension import ExtensionModule
    from stac_manager.modules.output import OutputModule
    from stac_manager.modules.validate import ValidateModule
    from stac_manager.modules.update import UpdateModule
    from stac_manager.modules.transform import TransformModule
    
    # IngestModule
    ingest = IngestModule({"mode": "api", "source": "https://fake.api"})
    assert hasattr(ingest, 'set_logger')
    ingest.set_logger(mock_logger)
    assert ingest.logger is mock_logger
    
    # ExtensionModule
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {"properties": {}}
        extension = ExtensionModule({"schema_uri": "https://example.com/schema.json"})
        assert hasattr(extension, 'set_logger')
        extension.set_logger(mock_logger)
        assert extension.logger is mock_logger
    
    # OutputModule
    output = OutputModule({"base_dir": "/tmp", "format": "json"})
    assert hasattr(output, 'set_logger')
    output.set_logger(mock_logger)
    assert output.logger is mock_logger
    
    # ValidateModule
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {"type": "object", "properties": {}}
        validate = ValidateModule({"schema_url": "https://example.com/schema.json"})
        assert hasattr(validate, 'set_logger')
        validate.set_logger(mock_logger)
        assert validate.logger is mock_logger
    
    # UpdateModule
    update = UpdateModule({"updates": {}})
    assert hasattr(update, 'set_logger')
    update.set_logger(mock_logger)
    assert update.logger is mock_logger
    
    # TransformModule (requires input_file)
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("id,value\ntest,123\n")
        temp_path = f.name
    
    try:
        transform = TransformModule({
            "input_file": temp_path,
            "field_mapping": {"properties.test": "value"}
        })
        assert hasattr(transform, 'set_logger')
        transform.set_logger(mock_logger)
        assert transform.logger is mock_logger
    finally:
        os.unlink(temp_path)
