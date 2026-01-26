"""Tests for StacManager orchestration."""
import pytest
from stac_manager.core.manager import MODULE_REGISTRY, load_module_class
from stac_manager.exceptions import ConfigurationError


def test_module_registry_contains_all_modules():
    """Test MODULE_REGISTRY contains all implemented modules."""
    expected_modules = [
        'IngestModule',
        'SeedModule',
        'TransformModule',
        'UpdateModule',
        'ExtensionModule',
        'ValidateModule',
        'OutputModule'
    ]
    
    for module_name in expected_modules:
        assert module_name in MODULE_REGISTRY


def test_load_module_class_valid():
    """Test loading a valid module class."""
    module_class = load_module_class('IngestModule')
    
    # Verify it's a class (not instance)
    assert isinstance(module_class, type)
    
    # Verify class name
    assert module_class.__name__ == 'IngestModule'


def test_load_module_class_invalid():
    """Test loading an unknown module raises error."""
    with pytest.raises(ConfigurationError) as exc_info:
        load_module_class('NonExistentModule')
    
    assert "unknown module" in str(exc_info.value).lower()
    assert "NonExistentModule" in str(exc_info.value)


def test_load_module_class_all_registered():
    """Test that all registered modules can be loaded."""
    for module_name in MODULE_REGISTRY.keys():
        module_class = load_module_class(module_name)
        assert module_class is not None
        assert module_class.__name__ == module_name
