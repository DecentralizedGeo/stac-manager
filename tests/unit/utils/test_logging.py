import logging
import json
import logging.handlers
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch
from stac_manager.utils.logging import setup_logger, JsonFormatter, LogRunContext, ShortPathFilter

@pytest.fixture
def clean_logger():
    """Ensure stac_manager logger is clean before and after tests."""
    logger = logging.getLogger("stac_manager")
    logger.handlers = []
    logger.setLevel(logging.NOTSET)
    return logger

def test_json_formatter_valid_json():
    """Test that JsonFormatter produces valid JSON with required fields."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="/path/to/file.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None
    )
    # Add short_path as the ShortPathFilter would
    record.short_path = "test.module"
    
    json_str = formatter.format(record)
    data = json.loads(json_str)
    
    assert data["message"] == "Test message"
    assert data["level"] == "INFO"
    assert data["logger"] == "test_logger"  # Changed from 'name' to 'logger'
    assert "timestamp" in data
    assert data["module"] == "test.module"  # Uses short_path if available
    assert data["line"] == 10

def test_setup_logger_creates_handlers(clean_logger, tmp_path):
    """Test that setup_logger creates both console and file handlers."""
    log_file = tmp_path / "test.log"
    config = {
        "settings": {
            "logging": {
                "level": "DEBUG",
                "file": str(log_file),
                "output_format": "json"
            }
        }
    }
    
    logger = setup_logger(config)
    
    assert len(logger.handlers) == 2
    assert logger.level == logging.DEBUG
    assert not logger.propagate
    
    # Check handlers types
    handlers = {type(h) for h in logger.handlers}
    assert logging.StreamHandler in handlers
    assert logging.handlers.RotatingFileHandler in handlers

def test_setup_logger_defaults(clean_logger):
    """Test setup_logger with empty config uses defaults."""
    config = {}
    
    # Mocking RotatingFileHandler to avoid file creation in default path
    with patch("stac_manager.utils.logging.RotatingFileHandler") as mock_handler:
        logger = setup_logger(config)
        
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 2 # Still adds both
        mock_handler.assert_called_once() # Should try to create default log file

def test_log_run_context_execution():
    """Test LogRunContext logs start and end messages."""
    logger = MagicMock(spec=logging.Logger)
    
    with LogRunContext(logger, "test-workflow", "config.yaml"):
        pass
        
    # Verify start logs
    assert logger.info.call_count >= 2 # Start banner + End banner
    
    # Check for specific content in calls
    calls = [call.args[0] for call in logger.info.call_args_list]
    start_msg = any("test-workflow" in str(msg) for msg in calls)
    end_msg = any("Runtime:" in str(msg) for msg in calls)
    
    assert start_msg
    assert end_msg


def test_short_path_filter():
    """Test ShortPathFilter converts paths to module notation."""
    # Create filter with a known base path
    from pathlib import Path
    base_path = Path("c:/test/project/src/stac_manager")
    path_filter = ShortPathFilter(base_path=base_path)
    
    # Create log record with full path
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="c:/test/project/src/stac_manager/core/manager.py",
        lineno=42,
        msg="Test",
        args=(),
        exc_info=None
    )
    
    # Apply filter
    path_filter.filter(record)
    
    # Should convert to dot notation
    assert hasattr(record, "short_path")
    assert record.short_path == "core.manager"


def test_short_path_filter_fallback():
    """Test ShortPathFilter falls back to filename for paths outside base."""
    from pathlib import Path
    base_path = Path("c:/test/project/src/stac_manager")
    path_filter = ShortPathFilter(base_path=base_path)
    
    # Create record with path outside base
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="c:/other/location/external.py",
        lineno=10,
        msg="Test",
        args=(),
        exc_info=None
    )
    
    path_filter.filter(record)
    
    # Should use just filename
    assert record.short_path == "external"


def test_log_run_context_success():
    """Test LogRunContext logs success message on clean exit."""
    logger = MagicMock(spec=logging.Logger)
    
    with LogRunContext(logger, "test-workflow"):
        pass  # Clean exit
    
    # Should call info for success, not error
    info_calls = [call.args[0] for call in logger.info.call_args_list]
    assert any("completed successfully" in str(msg).lower() for msg in info_calls)
    assert logger.error.call_count == 0


def test_log_run_context_system_exit_zero():
    """Test LogRunContext logs success for SystemExit(0)."""
    logger = MagicMock(spec=logging.Logger)
    
    try:
        with LogRunContext(logger, "test-workflow"):
            raise SystemExit(0)
    except SystemExit:
        pass
    
    # Should log success, not error
    info_calls = [call.args[0] for call in logger.info.call_args_list]
    assert any("completed successfully" in str(msg).lower() for msg in info_calls)
    assert logger.error.call_count == 0


def test_log_run_context_system_exit_nonzero():
    """Test LogRunContext logs error for SystemExit(1)."""
    logger = MagicMock(spec=logging.Logger)
    
    try:
        with LogRunContext(logger, "test-workflow"):
            raise SystemExit(1)
    except SystemExit:
        pass
    
    # Should log error
    assert logger.error.call_count == 1
    error_call = logger.error.call_args[0][0]
    assert "failed" in error_call.lower()
    assert "exit_code: 1" in error_call


def test_log_run_context_exception():
    """Test LogRunContext logs error for regular exceptions."""
    logger = MagicMock(spec=logging.Logger)
    
    try:
        with LogRunContext(logger, "test-workflow"):
            raise ValueError("Test error")
    except ValueError:
        pass
    
    # Should log error
    assert logger.error.call_count == 1
    error_call = logger.error.call_args[0][0]
    assert "failed" in error_call.lower()
    assert "ValueError" in error_call
    assert "Test error" in error_call

