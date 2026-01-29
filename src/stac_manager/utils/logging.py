import logging
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Any, Optional

class JsonFormatter(logging.Formatter):
    """JSON formatter for machine-readable file logging."""
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
            "path": record.pathname,
            "step_id": getattr(record, "step_id", "system")
        }
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)

def setup_logger(config: dict) -> logging.Logger:
    """
    Configure the 'stac_manager' logger with console and file handlers.
    
    Args:
        config: Workflow configuration dictionary with 'settings.logging' section.
        
    Returns:
        Configured logger instance.
    """
    log_config = config.get('settings', {}).get('logging', {})
    level_str = log_config.get('level', 'INFO').upper()
    level = getattr(logging, level_str, logging.INFO)
    
    logger = logging.getLogger("stac_manager")
    logger.setLevel(level)
    logger.handlers = []  # Clear existing handlers
    logger.propagate = False 
    
    # 1. Console Handler (Cleaner/Less Detailed for Humans)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(console_formatter)
    logger.addHandler(ch)
    
    # 2. File Handler (Detailed/JSON + Rotation for Machines/Debugging)
    # Default to 'logs/stac_manager.json' if not specific
    output_format = log_config.get('output_format', 'text').lower()
    
    default_filename = 'logs/stac_manager.json' if output_format == 'json' else 'logs/stac_manager.log'
    file_path_str = log_config.get('file', default_filename)
    log_path = Path(file_path_str)
    
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # maxBytes=10MB, backupCount=5
        fh = RotatingFileHandler(
            log_path, 
            maxBytes=10 * 1024 * 1024, 
            backupCount=5, 
            encoding='utf-8'
        )
        
        if output_format == 'json':
            fh.setFormatter(JsonFormatter())
        else:
            # Detailed text format for file
            file_text_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(pathname)s:%(lineno)d] - %(message)s'
            )
            fh.setFormatter(file_text_formatter)
            
        fh.setLevel(level)
        logger.addHandler(fh)
    except Exception as e:
        # Fallback to console warning if file logging fails (permissions, etc)
        # We use print here because the logger might not be fully set up
        print(f"WARNING: Could not create log file {log_path}: {e}")
            
    return logger

class LogRunContext:
    """Context manager for logging workflow execution boundaries."""
    
    def __init__(self, logger: logging.Logger, workflow_name: str, config_path: str = None):
        self.logger = logger
        self.workflow_name = workflow_name
        self.config_path = config_path
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        start_dt = datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')
        
        separator = "-" * 60
        self.logger.info(separator)
        self.logger.info(f"Start-time: {start_dt} | Workflow: {self.workflow_name}")
        if self.config_path:
            self.logger.info(f"Config: {self.config_path}")
        self.logger.info(separator)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        duration = end_time - self.start_time
        
        # Format Duration
        if duration < 60:
            duration_str = f"{duration:.2f}s"
        elif duration < 3600:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            duration_str = f"{minutes}m {seconds}s"
        else:
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            seconds = int(duration % 60)
            duration_str = f"{hours}h {minutes}m {seconds}s"

        end_dt = datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')
        
        separator = "-" * 60
        self.logger.info(separator)
        self.logger.info(f"End-time: {end_dt} | Runtime: {duration_str}")
        
        if exc_type:
            self.logger.error(f"Workflow failed with {exc_type.__name__}: {exc_val}")
        else:
            self.logger.info("Workflow completed successfully")
            
        self.logger.info(separator)
