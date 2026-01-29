import logging
import json
import logging.handlers
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch
from stac_manager.utils.logging import setup_logger, JsonFormatter, LogRunContext

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
    
    json_str = formatter.format(record)
    data = json.loads(json_str)
    
    assert data["message"] == "Test message"
    assert data["level"] == "INFO"
    assert data["name"] == "test_logger"
    assert "timestamp" in data
    assert data["path"] == "/path/to/file.py"
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
