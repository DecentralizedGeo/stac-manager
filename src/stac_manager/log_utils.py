
import logging
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Any, AsyncIterator

class JsonFormatter(logging.Formatter):
    """JSON formatter for file logging."""
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
            "path": record.pathname
        }
        return json.dumps(log_obj)

def setup_logger(config: dict) -> logging.Logger:
    # Grab logging config settings from the the settings section of the workflow config
    # Default to INFO if not specified
    log_config = config.get('settings', {}).get('logging', {})
    level_str = log_config.get('level', 'INFO').upper()
    level = getattr(logging, level_str, logging.INFO)
    
    logger = logging.getLogger("stac_manager")
    logger.setLevel(level)
    logger.handlers = [] # Clear existing
    logger.propagate = False 
    
    # 1. Console Handler (Cleaner/Less Detailed)
    # Simple format: Time - Level - Message
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(console_formatter)
    logger.addHandler(ch)
    
    # 2. File Handler (Detailed/JSON + Rotation)
    output_format = log_config.get('output_format', 'text').lower()
    
    # Default to 'logs/stac_manager.log' or .json based on format
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
            # Re-use console formatter or create a slightly more detailed text one for file
            file_text_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(file_text_formatter)
            
        fh.setLevel(level)
        logger.addHandler(fh)
    except Exception as e:
        print(f"WARNING: Could not create log file {log_path}: {e}")
            
    return logger

async def monitor_async_generator(source: AsyncIterator[Any], logger: logging.Logger, step_id: str) -> AsyncIterator[Any]:
    """
    Wraps an async generator to log its start, item count, and completion.
    """
    logger.info(f"[{step_id}] Pipeline started")
    count = 0
    try:
        async for item in source:
            count += 1
            yield item
    finally:
        logger.info(f"[{step_id}] Pipeline finished (yielded {count} items)")

class LogRunContext:
    def __init__(self, logger: logging.Logger, workflow_name: str, config_path: str = None):
        self.logger = logger
        self.workflow_name = workflow_name
        self.config_path = config_path
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        start_dt = datetime.fromtimestamp(self.start_time).strftime('%d/%m/%y %H:%M:%S')
        
        separator = "|---------------------------------------------------------"
        msg = [
            separator,
            f"|   Start-time: {start_dt} | Workflow: {self.workflow_name}",
        ]
        if self.config_path:
            msg.append(f"|   Config: {self.config_path}")
        msg.append(separator)
        
        # Log as a single block (or iterated lines)
        # Using a single call with newlines might mess up some formatters (like JSON),
        # but for text logs it looks good. Let's log line by line to be safe and clear.
        for line in msg:
            self.logger.info(line)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        duration = end_time - self.start_time
        end_dt = datetime.fromtimestamp(end_time).strftime('%d/%m/%y %H:%M:%S')
        
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

        separator = "|---------------------------------------------------------"
        msg = [
            separator,
            f"|   End-time: {end_dt} | Runtime: {duration_str}",
            separator
        ]
        
        for line in msg:
            self.logger.info(line)
