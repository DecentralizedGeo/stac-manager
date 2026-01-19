
import pytest
import logging
import json
import tempfile
import shutil
from pathlib import Path
from stac_manager.log_utils import setup_logger

def test_setup_logger_rotation_and_format():
    # Setup temporary directory for logs
    log_dir = Path(tempfile.mkdtemp())
    log_file = log_dir / "test.log"
    
    try:
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
        
        # Verify Handlers
        assert len(logger.handlers) >= 2
        
        # Verify File Handler Properties (Rotation)
        from logging.handlers import RotatingFileHandler
        file_handler = next(h for h in logger.handlers if isinstance(h, RotatingFileHandler))
        assert file_handler.maxBytes == 10 * 1024 * 1024
        assert file_handler.backupCount == 5
        
        # Log something
        logger.info("Test message", extra={"key": "value"})
        
        # Flush
        for h in logger.handlers:
            h.close()
            
        # Verify File Content (JSON)
        content = log_file.read_text(encoding='utf-8')
        log_json = json.loads(content.strip())
        assert log_json['message'] == "Test message"
        assert log_json['level'] == "INFO"
        
    finally:
        try:
            shutil.rmtree(log_dir)
        except:
            pass

def test_setup_logger_text_format_default():
    # Setup temporary directory for logs
    log_dir = Path(tempfile.mkdtemp())
    log_file = log_dir / "test_default.log"
    
    try:
        config = {
            "settings": {
                "logging": {
                    "level": "DEBUG",
                    "file": str(log_file)
                    # output_format defaults to text
                }
            }
        }
        
        logger = setup_logger(config)
        logger.info("Text message")
        
         # Flush
        for h in logger.handlers:
            h.close()
            
        content = log_file.read_text(encoding='utf-8')
        # Should be standard text format
        assert "INFO - Text message" in content
        assert "{" not in content # Minimal check ensuring it's not JSON
        
    finally:
        try:
            shutil.rmtree(log_dir)
        except:
            pass

from unittest.mock import patch

def test_default_filename_extension():
    # 1. Test JSON format default
    config_json = {
        "settings": {
            "logging": {
                "level": "INFO",
                "output_format": "json"
                # No file specified
            }
        }
    }
    
    with patch('stac_manager.log_utils.RotatingFileHandler') as MockHandler:
        setup_logger(config_json)
        # Verify call args
        args, _ = MockHandler.call_args
        # args[0] should be a Path object ending in .json
        assert str(args[0]).endswith("stac_manager.json")
        
    # 2. Test Text format default
    config_text = {
        "settings": {
            "logging": {
                "level": "INFO",
                "output_format": "text"
            }
        }
    }
    
    with patch('stac_manager.log_utils.RotatingFileHandler') as MockHandler:
        setup_logger(config_text)
        args, _ = MockHandler.call_args
        assert str(args[0]).endswith("stac_manager.log") 
