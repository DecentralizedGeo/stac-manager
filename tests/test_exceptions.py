import pytest
from stac_manager.exceptions import StacManagerError, ConfigurationError

def test_exception_inheritance():
    err = ConfigurationError("Bad config")
    assert isinstance(err, StacManagerError)
    assert str(err) == "Bad config"
