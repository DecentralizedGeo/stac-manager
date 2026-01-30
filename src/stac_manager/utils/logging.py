import logging
import sys
import json
import time
import os
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Any, Optional


class ShortPathFilter(logging.Filter):
    """Shorten file paths to module-relative paths for readable logs.
    
    Converts full paths like:
        C:\\Users\\user\\...\\stac_manager\\core\\manager.py

        or

        /home/user/.../stac_manager/core/manager.py

    To short module paths:
        core.manager
    """
    
    def __init__(self, base_path: str | Path | None = None):
        """Initialize filter with base path for relative resolution.
        
        Args:
            base_path: Base path to calculate relative paths from.
                      If None, auto-detects from this file's location.
        """
        super().__init__()
        
        # Find src/stac_manager/ directory
        if base_path is None:
            # Auto-detect from this file's location
            this_file = Path(__file__).resolve()
            # Walk up to find src/stac_manager/
            for parent in this_file.parents:
                if parent.name == 'stac_manager' and parent.parent.name == 'src':
                    base_path = parent
                    break
        
        self.base_path = Path(base_path) if base_path else None
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add short_path attribute to LogRecord.
        
        Args:
            record: Log record to process
            
        Returns:
            True (always allow record through)
        """
        if self.base_path:
            try:
                full_path = Path(record.pathname)
                # Get relative path from stac_manager/ root
                rel_path = full_path.relative_to(self.base_path)
                # Convert to dot notation: core/manager.py -> core.manager
                module_path = str(rel_path.with_suffix('')).replace(os.sep, '.')
                record.short_path = module_path
            except (ValueError, AttributeError):
                # Not under base_path, use filename only
                record.short_path = Path(record.pathname).stem
        else:
            record.short_path = Path(record.pathname).stem
        
        return True


class JsonFormatter(logging.Formatter):
    """JSON formatter for machine-readable file logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON string with log data
        """
        log_obj = {
            "timestamp": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
            "logger": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "module": getattr(record, "short_path", record.module),
            "line": record.lineno,
        }
        
        # Add custom fields if present
        if hasattr(record, "item_id"):
            log_obj["item_id"] = record.item_id
        if hasattr(record, "step_id"):
            log_obj["step_id"] = record.step_id
            
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)


def setup_logger(config: dict) -> logging.Logger:
    """Configure the 'stac_manager' logger with console and file handlers.
    
    Supports:
    - Short path formatting for readability
    - Configurable output format (text/json)
    - Configurable log level
    - Rotating file handler
    
    Args:
        config: Workflow configuration dictionary with 'settings.logging' section.
        
    Returns:
        Configured logger instance.
        
    Configuration Example:
        settings:
          logging:
            level: INFO
            output_format: text  # or 'json'
            progress_interval: 100
            file: logs/stac_manager.log
    """
    settings = config.get('settings') or {}
    log_config = settings.get('logging', {})
    level_str = log_config.get('level', 'INFO').upper()
    level = getattr(logging, level_str, logging.INFO)
    
    logger = logging.getLogger("stac_manager")
    logger.setLevel(level)
    logger.handlers = []  # Clear existing handlers
    logger.propagate = False 
    
    # Create path shortening filter
    path_filter = ShortPathFilter()
    
    # 1. Console Handler (Concise format for humans)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(short_path)s:%(lineno)d] - %(message)s',
        datefmt='%H:%M:%S'
    )
    ch = logging.StreamHandler(sys.stdout)
    # Set handler to DEBUG to allow all permitted records (filtering done by Loggers)
    ch.setLevel(logging.DEBUG)
    ch.addFilter(path_filter)
    ch.setFormatter(console_formatter)
    logger.addHandler(ch)
    
    # 2. File Handler (Detailed format, text or JSON)
    output_format = log_config.get('output_format', 'text').lower()
    
    # Default filename based on format
    default_filename = 'logs/stac_manager.json' if output_format == 'json' else 'logs/stac_manager.log'
    file_path_str = log_config.get('file', default_filename)
    log_path = Path(file_path_str)
    
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # maxBytes=10MB (default), backupCount=5 (default)
        # 'file_size' is in MB
        file_size_mb = log_config.get('file_size', 10)
        max_bytes = int(file_size_mb * 1024 * 1024)
            
        backup_count = log_config.get('backup_count', 5)
        
        fh = RotatingFileHandler(
            log_path, 
            maxBytes=max_bytes, 
            backupCount=backup_count, 
            encoding='utf-8'
        )
        
        if output_format == 'json':
            fh.setFormatter(JsonFormatter())
        else:
            # Detailed text format for file with short paths
            file_text_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(short_path)s:%(lineno)d] - %(message)s'
            )
            fh.setFormatter(file_text_formatter)
            
        # Set handler to DEBUG to allow all permitted records
        fh.setLevel(logging.DEBUG)
        fh.addFilter(path_filter)
        logger.addHandler(fh)
    except Exception as e:
        # Fallback to console warning if file logging fails (permissions, etc)
        # We use print here because the logger might not be fully set up
        print(f"WARNING: Could not create log file {log_path}: {e}")
            
    return logger


class LogRunContext:
    """Context manager for logging workflow execution boundaries.
    
    Logs start/end times, duration, and properly handles exit status including
    SystemExit codes.
    """
    
    def __init__(self, logger: logging.Logger, workflow_name: str, config_path: str = None):
        """Initialize context manager.
        
        Args:
            logger: Logger instance to use
            workflow_name: Name of workflow being executed
            config_path: Optional path to config file for logging
        """
        self.logger = logger
        self.workflow_name = workflow_name
        self.config_path = config_path
        self.start_time = None

    def __enter__(self):
        """Log workflow start."""
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
        """Log workflow completion with proper status handling.
        
        Correctly interprets:
        - SystemExit(0): Success (INFO)
        - SystemExit(non-zero): Failure (ERROR)
        - Other exceptions: Failure (ERROR)
        - No exception: Success (INFO)
        """
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
        
        # Handle exit status correctly
        if exc_type is None:
            # Clean exit, no exception
            self.logger.info("Workflow completed successfully")
        elif exc_type is SystemExit:
            # SystemExit: Check exit code
            exit_code = exc_val.code if hasattr(exc_val, 'code') else exc_val
            if exit_code == 0 or exit_code is None:
                self.logger.info("Workflow completed successfully | exit_code: 0")
            else:
                self.logger.error(f"Workflow failed | exit_code: {exit_code}")
        else:
            # Real exception
            self.logger.error(
                f"Workflow failed | exception: {exc_type.__name__} | message: {exc_val}"
            )
            
        self.logger.info(separator)

