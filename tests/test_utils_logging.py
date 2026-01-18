import os
import logging
from stac_manager.logging import setup_logger
from stac_manager.utils import substitute_env_vars
from stac_manager.exceptions import ConfigurationError
import pytest

def test_substitute_env_vars():
    os.environ["TEST_VAR"] = "secret"
    config = {"key": "${TEST_VAR}", "other": "value"}
    resolved = substitute_env_vars(config)
    assert resolved["key"] == "secret"
    assert resolved["other"] == "value"

def test_substitute_env_vars_missing():
    with pytest.raises(ConfigurationError):
        substitute_env_vars({"key": "${MISSING_VAR}"})

def test_setup_logger(tmp_path):
    log_file = tmp_path / "test.log"
    config = {
        "logging": {
            "level": "DEBUG",
            "file": str(log_file)
        }
    }
    logger = setup_logger(config)
    assert logger.level == logging.DEBUG
    # Log something
    logger.info("Test message")
    # Verify file created
    assert log_file.exists()
