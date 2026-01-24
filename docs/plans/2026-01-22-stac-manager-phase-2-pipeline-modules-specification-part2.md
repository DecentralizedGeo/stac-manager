# STAC Manager Phase 2 (Pipeline Modules) Implementation Plan - Part 2

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

> **Context**: This is **Part 2 of Phase 2: Pipeline Modules** of the STAC Manager implementation.  
> See [Implementation Roadmap](./2026-01-22-stac-manager-roadmap.md) and [Part 1](./2026-01-22-stac-manager-phase-2-pipeline-modules-specification-part1.md) for complete context.

**Goal**: Implement complex modifier modules (ValidateModule, ExtensionModule, TransformModule) that perform schema validation, extension scaffolding, and data enrichment operations.

**Architecture**: Modifier protocol implementation with schema-driven transformations
- **ValidateModule**: STAC schema validation using stac-validator
- **ExtensionModule**: JSON Schema-based extension scaffolding
- **TransformModule**: Sidecar data enrichment with field mapping

**Tech Stack**: 
- Python 3.12+, stac-validator, jsonschema, requests (schema fetching)
- pandas/pyarrow (CSV/Parquet sidecar reading), JMESPath (field mapping)
- pytest, pytest-asyncio, pytest-cov

**Dependencies**: 
- Part 1 complete (Core Infrastructure, SeedModule, UpdateModule)
- Phase 1 utilities (`stac_manager/utils/`)

**Learnings from Part 1**:
- Use `deep_merge` with strategies: `keep_existing`, `overwrite`, `update_only`
- Dot-notation format for all patch/mapping files (not deep dict structures)
- Protocol compliance testing: `assert isinstance(module, Protocol)`
- Error handling: Native exceptions → DataProcessingError (Tier 2)

---

## Table of Contents

### Phase 4: Validate Module (Tasks 18-21) - 4 tasks
STAC schema validation with stac-validator integration

### Phase 5: Extension Module (Tasks 22-27) - 6 tasks  
JSON Schema-based extension scaffolding and application

### Phase 6: Transform Module (Tasks 28-35) - 8 tasks
Sidecar data enrichment, field mapping, and merge strategies

**Total Tasks**: 18 granular TDD tasks

---

## Phase 4: Validate Module

### Task 18: Validate Module - Basic Validation

**Files:**
- Create: `src/stac_manager/modules/validate.py`
- Create: `tests/unit/modules/test_validate.py`

**Step 1: Write failing test for basic STAC validation**

Create `tests/unit/modules/test_validate.py`:

```python
import pytest
from stac_manager.modules.validate import ValidateModule
from tests.fixtures.context import MockWorkflowContext
from tests.fixtures.stac_items import VALID_ITEM


def test_validate_module_passes_valid_item():
    """ValidateModule passes valid STAC items."""
    module = ValidateModule({"strict": False})
    context = MockWorkflowContext.create()
    
    result = module.modify(VALID_ITEM.copy(), context)
    
    assert result is not None
    assert result["id"] == "test-item-001"


def test_validate_module_rejects_invalid_item():
    """ValidateModule returns None for invalid items in permissive mode."""
    module = ValidateModule({"strict": False})
    context = MockWorkflowContext.create()
    
    invalid_item = {"id": "test"}  # Missing required STAC fields
    
    result = module.modify(invalid_item, context)
    
    assert result is None
    assert len(context.failure_collector.failures) == 1
    assert "validation" in context.failure_collector.failures[0]["error"].lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_validate.py::test_validate_module_passes_valid_item -v`  
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `src/stac_manager/modules/validate.py`:

```python
"""Validate Module - STAC schema validation."""
from stac_manager.modules.config import ValidateConfig
from stac_manager.core.context import WorkflowContext
from stac_validator import stac_validator


class ValidateModule:
    """Validates STAC Items against schema."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with configuration."""
        self.config = ValidateConfig(**config)
        # Initialize validator once
        self.validator = stac_validator.StacValidate()
    
    def modify(self, item: dict, context: WorkflowContext) -> dict | None:
        """
        Validate item against STAC schema.
        
        Args:
            item: STAC item dict
            context: Workflow context
        
        Returns:
            Item if valid, None if invalid (permissive mode)
        """
        # Validate item
        is_valid = self.validator.validate_dict(item)
        
        if not is_valid:
            error_msg = "; ".join(self.validator.message) if hasattr(self.validator, 'message') else "Validation failed"
            
            context.failure_collector.add(
                item_id=item.get("id", "unknown"),
                error=f"STAC validation failed: {error_msg}",
                step_id="validate"
            )
            
            return None  # Drop invalid item
        
        return item
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_validate.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/validate.py tests/unit/modules/test_validate.py
git commit -m "feat(modules): add basic ValidateModule implementation"
```

---

### Task 19: Validate Module - Strict vs Permissive Mode

**Files:**
- Modify: `tests/unit/modules/test_validate.py`
- Modify: `src/stac_manager/modules/validate.py`

**Step 1: Write test for strict mode**

Add to `tests/unit/modules/test_validate.py`:

```python
from stac_manager.exceptions import DataProcessingError


def test_validate_module_strict_mode_raises():
    """ValidateModule raises error for invalid items in strict mode."""
    module = ValidateModule({"strict": True})
    context = MockWorkflowContext.create()
    
    invalid_item = {"id": "test"}
    
    with pytest.raises(DataProcessingError) as exc_info:
        module.modify(invalid_item, context)
    
    assert "validation failed" in str(exc_info.value).lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_validate.py::test_validate_module_strict_mode_raises -v`  
Expected: FAIL (strict mode not implemented)

**Step 3: Implement strict mode**

Update `src/stac_manager/modules/validate.py`:

```python
"""Validate Module - STAC schema validation."""
from stac_manager.modules.config import ValidateConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import DataProcessingError
from stac_validator import stac_validator


class ValidateModule:
    """Validates STAC Items against schema."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with configuration."""
        self.config = ValidateConfig(**config)
        self.validator = stac_validator.StacValidate()
    
    def modify(self, item: dict, context: WorkflowContext) -> dict | None:
        """
        Validate item against STAC schema.
        
        Args:
            item: STAC item dict
            context: Workflow context
        
        Returns:
            Item if valid, None if invalid (permissive mode)
        
        Raises:
            DataProcessingError: If strict=True and validation fails
        """
        is_valid = self.validator.validate_dict(item)
        
        if not is_valid:
            error_msg = "; ".join(self.validator.message) if hasattr(self.validator, 'message') else "Validation failed"
            
            if self.config.strict:
                raise DataProcessingError(f"STAC validation failed: {error_msg}")
            
            context.failure_collector.add(
                item_id=item.get("id", "unknown"),
                error=f"STAC validation failed: {error_msg}",
                step_id="validate"
            )
            
            return None
        
        return item
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_validate.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/validate.py tests/unit/modules/test_validate.py
git commit -m "feat(modules): add strict mode to ValidateModule"
```

---

### Task 20: Validate Module - Extension Schema Support

**Files:**
- Modify: `tests/unit/modules/test_validate.py`
- Modify: `src/stac_manager/modules/validate.py`

**Step 1: Write test for extension validation**

Add to `tests/unit/modules/test_validate.py`:

```python
def test_validate_module_with_extension_schemas():
    """ValidateModule validates against extension schemas."""
    module = ValidateModule({
        "extension_schemas": ["https://stac-extensions.github.io/eo/v1.1.0/schema.json"]
    })
    context = MockWorkflowContext.create()
    
    item = VALID_ITEM.copy()
    item["stac_extensions"] = ["https://stac-extensions.github.io/eo/v1.1.0/schema.json"]
    item["properties"]["eo:cloud_cover"] = 15.5
    
    result = module.modify(item, context)
    
    assert result is not None
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/unit/modules/test_validate.py::test_validate_module_with_extension_schemas -v`  
Expected: PASS (stac-validator handles extensions automatically)

**Step 3: Commit**

```bash
git add tests/unit/modules/test_validate.py
git commit -m "test(modules): verify extension schema validation"
```

---

### Task 21: Validate Module - Protocol Compliance

**Files:**
- Modify: `tests/unit/modules/test_validate.py`
- Modify: `src/stac_manager/modules/__init__.py`

**Step 1: Write protocol compliance test**

Add to `tests/unit/modules/test_validate.py`:

```python
from stac_manager.protocols import Modifier


def test_validate_module_implements_modifier_protocol():
    """ValidateModule implements Modifier protocol."""
    module = ValidateModule({})
    assert isinstance(module, Modifier)
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/unit/modules/test_validate.py::test_validate_module_implements_modifier_protocol -v`  
Expected: PASS

**Step 3: Add module exports**

Update `src/stac_manager/modules/__init__.py`:

```python
"""Pipeline module implementations."""
from stac_manager.modules.seed import SeedModule
from stac_manager.modules.update import UpdateModule
from stac_manager.modules.validate import ValidateModule

__all__ = [
    'SeedModule',
    'UpdateModule',
    'ValidateModule',
]
```

**Step 4: Run full test suite**

Run: `pytest tests/unit/modules/ -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/__init__.py tests/unit/modules/test_validate.py
git commit -m "feat(modules): complete ValidateModule with protocol compliance"
```

---

## Phase 5: Extension Module

### Task 22: Extension Module - Schema Fetching

**Files:**
- Create: `src/stac_manager/modules/extension.py`
- Create: `tests/unit/modules/test_extension.py`

**Step 1: Write failing test for schema download**

Create `tests/unit/modules/test_extension.py`:

```python
import pytest
import requests_mock
from stac_manager.modules.extension import ExtensionModule
from tests.fixtures.context import MockWorkflowContext
from stac_manager.exceptions import ConfigurationError


SIMPLE_SCHEMA = {
    "type": "object",
    "properties": {
        "properties": {
            "type": "object",
            "properties": {
                "test:field": {"type": "string"}
            }
        }
    }
}


def test_extension_module_fetches_schema():
    """ExtensionModule fetches schema from URI during init."""
    with requests_mock.Mocker() as m:
        m.get("https://example.com/schema.json", json=SIMPLE_SCHEMA)
        
        module = ExtensionModule({
            "schema_uri": "https://example.com/schema.json"
        })
        
        assert module.schema is not None
        assert "properties" in module.schema


def test_extension_module_schema_fetch_failure():
    """ExtensionModule raises ConfigurationError on fetch failure."""
    with requests_mock.Mocker() as m:
        m.get("https://example.com/missing.json", status_code=404)
        
        with pytest.raises(ConfigurationError) as exc_info:
            ExtensionModule({"schema_uri": "https://example.com/missing.json"})
        
        assert "schema" in str(exc_info.value).lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_extension.py::test_extension_module_fetches_schema -v`  
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Implement schema fetching**

Create `src/stac_manager/modules/extension.py`:

```python
"""Extension Module - STAC extension scaffolding."""
import requests
from stac_manager.modules.config import ExtensionConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import ConfigurationError


class ExtensionModule:
    """Applies STAC extensions via schema scaffolding."""
    
    def __init__(self, config: dict) -> None:
        """Initialize and fetch schema."""
        self.config = ExtensionConfig(**config)
        
        # Fetch schema
        try:
            response = requests.get(self.config.schema_uri, timeout=10)
            response.raise_for_status()
            self.schema = response.json()
        except requests.RequestException as e:
            raise ConfigurationError(f"Failed to fetch schema from {self.config.schema_uri}: {e}")
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_extension.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/extension.py tests/unit/modules/test_extension.py
git commit -m "feat(modules): add schema fetching to ExtensionModule"
```

---

### Task 23: Extension Module - Template Building (Simple Properties)

**Files:**
- Modify: `tests/unit/modules/test_extension.py`
- Modify: `src/stac_manager/modules/extension.py`

**Step 1: Write test for template building**

Add to `tests/unit/modules/test_extension.py`:

```python
def test_extension_module_builds_template():
    """ExtensionModule builds template from schema properties."""
    with requests_mock.Mocker() as m:
        m.get("https://example.com/schema.json", json=SIMPLE_SCHEMA)
        
        module = ExtensionModule({
            "schema_uri": "https://example.com/schema.json"
        })
        
        assert module.template is not None
        assert "properties" in module.template
        assert "test:field" in module.template["properties"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_extension.py::test_extension_module_builds_template -v`  
Expected: FAIL (template not built)

**Step 3: Implement template builder**

Update `src/stac_manager/modules/extension.py`:

```python
"""Extension Module - STAC extension scaffolding."""
import requests
from stac_manager.modules.config import ExtensionConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import ConfigurationError


class ExtensionModule:
    """Applies STAC extensions via schema scaffolding."""
    
    def __init__(self, config: dict) -> None:
        """Initialize and fetch schema."""
        self.config = ExtensionConfig(**config)
        
        # Fetch schema
        try:
            response = requests.get(self.config.schema_uri, timeout=10)
            response.raise_for_status()
            self.schema = response.json()
        except requests.RequestException as e:
            raise ConfigurationError(f"Failed to fetch schema from {self.config.schema_uri}: {e}")
        
        # Build template
        self.template = self._build_template(self.schema)
    
    def _build_template(self, schema: dict) -> dict:
        """
        Parse JSON Schema to build scaffolding template.
        
        Args:
            schema: JSON Schema dict
        
        Returns:
            Template dict with null values
        """
        template = {"properties": {}}
        
        # Extract properties from schema
        if "properties" in schema:
            schema_props = schema["properties"]
            if "properties" in schema_props and "properties" in schema_props["properties"]:
                # Nested structure: schema.properties.properties.properties
                target_props = schema_props["properties"]["properties"]
                
                for key, field_def in target_props.items():
                    default_val = field_def.get("default", None)
                    template["properties"][key] = default_val
        
        return template
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_extension.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/extension.py tests/unit/modules/test_extension.py
git commit -m "feat(modules): add template builder to ExtensionModule"
```

---

### Task 24: Extension Module - Template Building (oneOf Heuristic)

**Files:**
- Modify: `tests/unit/modules/test_extension.py`
- Modify: `src/stac_manager/modules/extension.py`

**Step 1: Write test for oneOf schema parsing**

Add to `tests/unit/modules/test_extension.py`:

```python
ONEOF_SCHEMA = {
    "oneOf": [
        {
            "properties": {
                "type": {"const": "Feature"},
                "properties": {
                    "properties": {
                        "custom:value": {"type": "number"}
                    }
                }
            }
        }
    ]
}


def test_extension_module_handles_oneof():
    """ExtensionModule parses oneOf schemas."""
    with requests_mock.Mocker() as m:
        m.get("https://example.com/oneof.json", json=ONEOF_SCHEMA)
        
        module = ExtensionModule({
            "schema_uri": "https://example.com/oneof.json"
        })
        
        assert "custom:value" in module.template["properties"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_extension.py::test_extension_module_handles_oneof -v`  
Expected: FAIL (oneOf not handled)

**Step 3: Implement oneOf handling**

Update `_build_template` in `src/stac_manager/modules/extension.py`:

```python
    def _build_template(self, schema: dict) -> dict:
        """Parse JSON Schema to build scaffolding template."""
        template = {"properties": {}}
        
        target_props = {}
        
        # Handle direct properties
        if "properties" in schema:
            schema_props = schema["properties"]
            if "properties" in schema_props and "properties" in schema_props["properties"]:
                target_props = schema_props["properties"]["properties"]
        
        # Handle oneOf variants
        elif "oneOf" in schema:
            for variant in schema["oneOf"]:
                if variant.get("properties", {}).get("type", {}).get("const") == "Feature":
                    # Found STAC Item definition
                    if "properties" in variant.get("properties", {}):
                        props_def = variant["properties"]["properties"]
                        if "properties" in props_def:
                            target_props = props_def["properties"]
                    break
        
        # Build template from extracted properties
        for key, field_def in target_props.items():
            default_val = field_def.get("default", None)
            template["properties"][key] = default_val
        
        return template
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_extension.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/extension.py tests/unit/modules/test_extension.py
git commit -m "feat(modules): add oneOf schema support to ExtensionModule"
```

---

### Task 25: Extension Module - Defaults Overlay

**Files:**
- Modify: `tests/unit/modules/test_extension.py`
- Modify: `src/stac_manager/modules/extension.py`

**Step 1: Write test for defaults application**

Add to `tests/unit/modules/test_extension.py`:

```python
def test_extension_module_applies_defaults():
    """ExtensionModule overlays user defaults onto template."""
    with requests_mock.Mocker() as m:
        m.get("https://example.com/schema.json", json=SIMPLE_SCHEMA)
        
        module = ExtensionModule({
            "schema_uri": "https://example.com/schema.json",
            "defaults": {
                "properties": {
                    "test:field": "custom_value"
                }
            }
        })
        
        assert module.template["properties"]["test:field"] == "custom_value"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_extension.py::test_extension_module_applies_defaults -v`  
Expected: FAIL (defaults not applied)

**Step 3: Implement defaults overlay**

Update `__init__` in `src/stac_manager/modules/extension.py`:

```python
"""Extension Module - STAC extension scaffolding."""
import requests
from stac_manager.modules.config import ExtensionConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import ConfigurationError
from stac_manager.utils.field_ops import deep_merge


class ExtensionModule:
    """Applies STAC extensions via schema scaffolding."""
    
    def __init__(self, config: dict) -> None:
        """Initialize and fetch schema."""
        self.config = ExtensionConfig(**config)
        
        # Fetch schema
        try:
            response = requests.get(self.config.schema_uri, timeout=10)
            response.raise_for_status()
            self.schema = response.json()
        except requests.RequestException as e:
            raise ConfigurationError(f"Failed to fetch schema from {self.config.schema_uri}: {e}")
        
        # Build template
        self.template = self._build_template(self.schema)
        
        # Apply user defaults over template
        if self.config.defaults:
            self.template = deep_merge(self.template, self.config.defaults, strategy='overwrite')
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_extension.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/extension.py tests/unit/modules/test_extension.py
git commit -m "feat(modules): add defaults overlay to ExtensionModule"
```

---

### Task 26: Extension Module - Item Tagging & Merging

**Files:**
- Modify: `tests/unit/modules/test_extension.py`
- Modify: `src/stac_manager/modules/extension.py`

**Step 1: Write test for extension application**

Add to `tests/unit/modules/test_extension.py`:

```python
from tests.fixtures.stac_items import VALID_ITEM


def test_extension_module_applies_to_item():
    """ExtensionModule tags and merges template into item."""
    with requests_mock.Mocker() as m:
        m.get("https://example.com/schema.json", json=SIMPLE_SCHEMA)
        
        module = ExtensionModule({
            "schema_uri": "https://example.com/schema.json",
            "defaults": {"properties": {"test:field": "value"}}
        })
        context = MockWorkflowContext.create()
        
        item = VALID_ITEM.copy()
        result = module.modify(item, context)
        
        # Check tagging
        assert "stac_extensions" in result
        assert "https://example.com/schema.json" in result["stac_extensions"]
        
        # Check scaffolding applied
        assert result["properties"]["test:field"] == "value"
        
        # Check existing data preserved
        assert result["properties"]["datetime"] == "2024-01-01T00:00:00Z"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_extension.py::test_extension_module_applies_to_item -v`  
Expected: FAIL (modify not implemented)

**Step 3: Implement modify method**

Add to `src/stac_manager/modules/extension.py`:

```python
    def modify(self, item: dict, context: WorkflowContext) -> dict:
        """
        Apply extension to item.
        
        Args:
            item: STAC item dict
            context: Workflow context
        
        Returns:
            Item with extension applied
        """
        # 1. Tag extension
        if "stac_extensions" not in item:
            item["stac_extensions"] = []
        
        if self.config.schema_uri not in item["stac_extensions"]:
            item["stac_extensions"].append(self.config.schema_uri)
        
        # 2. Merge template (keep existing values)
        item = deep_merge(item, self.template, strategy='keep_existing')
        
        return item
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_extension.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/extension.py tests/unit/modules/test_extension.py
git commit -m "feat(modules): add item tagging and merging to ExtensionModule"
```

---

### Task 27: Extension Module - Protocol Compliance

**Files:**
- Modify: `tests/unit/modules/test_extension.py`
- Modify: `src/stac_manager/modules/__init__.py`

**Step 1: Write protocol compliance test**

Add to `tests/unit/modules/test_extension.py`:

```python
from stac_manager.protocols import Modifier


def test_extension_module_implements_modifier_protocol():
    """ExtensionModule implements Modifier protocol."""
    with requests_mock.Mocker() as m:
        m.get("https://example.com/schema.json", json=SIMPLE_SCHEMA)
        
        module = ExtensionModule({"schema_uri": "https://example.com/schema.json"})
        assert isinstance(module, Modifier)
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/unit/modules/test_extension.py::test_extension_module_implements_modifier_protocol -v`  
Expected: PASS

**Step 3: Add module exports**

Update `src/stac_manager/modules/__init__.py`:

```python
"""Pipeline module implementations."""
from stac_manager.modules.seed import SeedModule
from stac_manager.modules.update import UpdateModule
from stac_manager.modules.validate import ValidateModule
from stac_manager.modules.extension import ExtensionModule

__all__ = [
    'SeedModule',
    'UpdateModule',
    'ValidateModule',
    'ExtensionModule',
]
```

**Step 4: Run full test suite**

Run: `pytest tests/unit/modules/ -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/__init__.py tests/unit/modules/test_extension.py
git commit -m "feat(modules): complete ExtensionModule with protocol compliance"
```

---

## Phase 6: Transform Module

### Task 28: Transform Module - Sidecar File Loading

**Files:**
- Create: `src/stac_manager/modules/transform.py`
- Create: `tests/unit/modules/test_transform.py`

**Step 1: Write test for JSON sidecar loading**

Create `tests/unit/modules/test_transform.py`:

```python
import pytest
import tempfile
import json
from stac_manager.modules.transform import TransformModule
from tests.fixtures.context import MockWorkflowContext


def test_transform_module_loads_json_sidecar():
    """TransformModule loads JSON sidecar file."""
    sidecar_data = [
        {"id": "item-001", "custom_field": "value1"},
        {"id": "item-002", "custom_field": "value2"}
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sidecar_data, f)
        temp_path = f.name
    
    try:
        module = TransformModule({"input_file": temp_path})
        
        assert module.sidecar_index is not None
        assert len(module.sidecar_index) == 2
    finally:
        import os
        os.unlink(temp_path)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_transform.py::test_transform_module_loads_json_sidecar -v`  
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Implement sidecar loading**

Create `src/stac_manager/modules/transform.py`:

```python
"""Transform Module - Sidecar data enrichment."""
import json
from pathlib import Path
from stac_manager.modules.config import TransformConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import ConfigurationError


class TransformModule:
    """Enriches items with sidecar data."""
    
    def __init__(self, config: dict) -> None:
        """Initialize and load sidecar file."""
        self.config = TransformConfig(**config)
        self.sidecar_index: dict[str, dict] = {}
        
        # Load sidecar file
        if self.config.input_file:
            file_path = Path(self.config.input_file)
            if not file_path.exists():
                raise ConfigurationError(f"input_file not found: {self.config.input_file}")
            
            with open(file_path, 'r') as f:
                self.sidecar_data = json.load(f)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/modules/test_transform.py::test_transform_module_loads_json_sidecar -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/transform.py tests/unit/modules/test_transform.py
git commit -m "feat(modules): add sidecar file loading to TransformModule"
```

---

### Task 29: Transform Module - Sidecar Indexing (Dict Input)

**Files:**
- Modify: `tests/unit/modules/test_transform.py`
- Modify: `src/stac_manager/modules/transform.py`

**Step 1: Write test for dict indexing**

Add to `tests/unit/modules/test_transform.py`:

```python
def test_transform_module_indexes_dict_sidecar():
    """TransformModule treats dict keys as IDs."""
    sidecar_data = {
        "item-001": {"custom_field": "value1"},
        "item-002": {"custom_field": "value2"}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sidecar_data, f)
        temp_path = f.name
    
    try:
        module = TransformModule({"input_file": temp_path})
        
        assert "item-001" in module.sidecar_index
        assert module.sidecar_index["item-001"]["custom_field"] == "value1"
    finally:
        import os
        os.unlink(temp_path)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_transform.py::test_transform_module_indexes_dict_sidecar -v`  
Expected: FAIL (dict indexing not implemented)

**Step 3: Implement dict indexing**

Update `__init__` in `src/stac_manager/modules/transform.py`:

```python
    def __init__(self, config: dict) -> None:
        """Initialize and load sidecar file."""
        self.config = TransformConfig(**config)
        self.sidecar_index: dict[str, dict] = {}
        
        # Load sidecar file
        if self.config.input_file:
            file_path = Path(self.config.input_file)
            if not file_path.exists():
                raise ConfigurationError(f"input_file not found: {self.config.input_file}")
            
            with open(file_path, 'r') as f:
                sidecar_data = json.load(f)
            
            # Build index
            if isinstance(sidecar_data, dict):
                # Dict: keys are IDs
                self.sidecar_index = sidecar_data
            elif isinstance(sidecar_data, list):
                # List: will implement in next task
                pass
            else:
                raise ConfigurationError("input_file must be JSON dict or list")
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_transform.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/transform.py tests/unit/modules/test_transform.py
git commit -m "feat(modules): add dict sidecar indexing to TransformModule"
```

---

### Task 30: Transform Module - Sidecar Indexing (List Input)

**Files:**
- Modify: `tests/unit/modules/test_transform.py`
- Modify: `src/stac_manager/modules/transform.py`

**Step 1: Write test for list indexing with JMESPath**

Add to `tests/unit/modules/test_transform.py`:

```python
def test_transform_module_indexes_list_sidecar():
    """TransformModule extracts IDs from list using JMESPath."""
    sidecar_data = [
        {"item_id": "item-001", "custom_field": "value1"},
        {"item_id": "item-002", "custom_field": "value2"}
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sidecar_data, f)
        temp_path = f.name
    
    try:
        module = TransformModule({
            "input_file": temp_path,
            "sidecar_id_path": "item_id"
        })
        
        assert "item-001" in module.sidecar_index
        assert module.sidecar_index["item-001"]["custom_field"] == "value1"
    finally:
        import os
        os.unlink(temp_path)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_transform.py::test_transform_module_indexes_list_sidecar -v`  
Expected: FAIL (list indexing not implemented)

**Step 3: Implement list indexing**

Update `__init__` in `src/stac_manager/modules/transform.py`:

```python
"""Transform Module - Sidecar data enrichment."""
import json
from pathlib import Path
import jmespath
from stac_manager.modules.config import TransformConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import ConfigurationError


class TransformModule:
    """Enriches items with sidecar data."""
    
    def __init__(self, config: dict) -> None:
        """Initialize and load sidecar file."""
        self.config = TransformConfig(**config)
        self.sidecar_index: dict[str, dict] = {}
        
        # Load sidecar file
        if self.config.input_file:
            file_path = Path(self.config.input_file)
            if not file_path.exists():
                raise ConfigurationError(f"input_file not found: {self.config.input_file}")
            
            with open(file_path, 'r') as f:
                sidecar_data = json.load(f)
            
            # Build index
            if isinstance(sidecar_data, dict):
                # Dict: keys are IDs
                self.sidecar_index = sidecar_data
            elif isinstance(sidecar_data, list):
                # List: extract ID from each record
                for record in sidecar_data:
                    record_id = jmespath.search(self.config.sidecar_id_path, record)
                    if record_id:
                        self.sidecar_index[record_id] = record
            else:
                raise ConfigurationError("input_file must be JSON dict or list")
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_transform.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/transform.py tests/unit/modules/test_transform.py
git commit -m "feat(modules): add list sidecar indexing with JMESPath"
```

---

### Task 31: Transform Module - Basic Enrichment

**Files:**
- Modify: `tests/unit/modules/test_transform.py`
- Modify: `src/stac_manager/modules/transform.py`

**Step 1: Write test for item enrichment**

Add to `tests/unit/modules/test_transform.py`:

```python
from tests.fixtures.stac_items import VALID_ITEM


def test_transform_module_enriches_item():
    """TransformModule merges sidecar data into item."""
    sidecar_data = {
        "test-item-001": {
            "properties": {
                "custom_field": "enriched_value"
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sidecar_data, f)
        temp_path = f.name
    
    try:
        module = TransformModule({
            "input_file": temp_path,
            "strategy": "merge"
        })
        context = MockWorkflowContext.create()
        
        item = VALID_ITEM.copy()
        result = module.modify(item, context)
        
        assert result["properties"]["custom_field"] == "enriched_value"
        assert result["properties"]["datetime"] == "2024-01-01T00:00:00Z"  # Preserved
    finally:
        import os
        os.unlink(temp_path)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_transform.py::test_transform_module_enriches_item -v`  
Expected: FAIL (modify not implemented)

**Step 3: Implement modify method**

Add to `src/stac_manager/modules/transform.py`:

```python
"""Transform Module - Sidecar data enrichment."""
import json
from pathlib import Path
import jmespath
from stac_manager.modules.config import TransformConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import ConfigurationError
from stac_manager.utils.field_ops import deep_merge


class TransformModule:
    """Enriches items with sidecar data."""
    
    def __init__(self, config: dict) -> None:
        """Initialize and load sidecar file."""
        self.config = TransformConfig(**config)
        self.sidecar_index: dict[str, dict] = {}
        
        # Load sidecar file
        if self.config.input_file:
            file_path = Path(self.config.input_file)
            if not file_path.exists():
                raise ConfigurationError(f"input_file not found: {self.config.input_file}")
            
            with open(file_path, 'r') as f:
                sidecar_data = json.load(f)
            
           # Build index
            if isinstance(sidecar_data, dict):
                self.sidecar_index = sidecar_data
            elif isinstance(sidecar_data, list):
                for record in sidecar_data:
                    record_id = jmespath.search(self.config.sidecar_id_path, record)
                    if record_id:
                        self.sidecar_index[record_id] = record
            else:
                raise ConfigurationError("input_file must be JSON dict or list")
    
    def modify(self, item: dict, context: WorkflowContext) -> dict:
        """
        Enrich item with sidecar data.
        
        Args:
            item: STAC item dict
            context: Workflow context
        
        Returns:
            Enriched item
        """
        item_id = item.get("id")
        if not item_id or item_id not in self.sidecar_index:
            return item
        
        # Get sidecar data for this item
        sidecar_record = self.sidecar_index[item_id]
        
        # Merge based on strategy
        if self.config.strategy == "merge":
            item = deep_merge(item, sidecar_record, strategy='overwrite')
        elif self.config.strategy == "update":
            item = deep_merge(item, sidecar_record, strategy='update_only')
        
        return item
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_transform.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/transform.py tests/unit/modules/test_transform.py
git commit -m "feat(modules): add item enrichment to TransformModule"
```

---

### Task 32: Transform Module - Update Strategy Testing

**Files:**
- Modify: `tests/unit/modules/test_transform.py`

**Step 1: Write test for update strategy**

Add to `tests/unit/modules/test_transform.py`:

```python
def test_transform_module_update_strategy():
    """TransformModule update strategy only modifies existing keys."""
    sidecar_data = {
        "test-item-001": {
            "properties": {
                "datetime": "2025-01-01T00:00:00Z",  # Existing key - should update
                "new_field": "should_be_ignored"      # New key - should be ignored
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sidecar_data, f)
        temp_path = f.name
    
    try:
        module = TransformModule({
            "input_file": temp_path,
            "strategy": "update"
        })
        context = MockWorkflowContext.create()
        
        item = VALID_ITEM.copy()
        original_datetime = item["properties"]["datetime"]
        
        result = module.modify(item, context)
        
        # Should update existing key
        assert result["properties"]["datetime"] == "2025-01-01T00:00:00Z"
        assert result["properties"]["datetime"] != original_datetime
        
        # Should NOT add new key
        assert "new_field" not in result["properties"]
    finally:
        import os
        os.unlink(temp_path)
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/unit/modules/test_transform.py::test_transform_module_update_strategy -v`  
Expected: PASS (already implemented via update_only in deep_merge)

**Step 3: Commit**

```bash
git add tests/unit/modules/test_transform.py
git commit -m "test(modules): verify update strategy in TransformModule"
```

---

### Task 33: Transform Module - Missing Item Handling

**Files:**
- Modify: `tests/unit/modules/test_transform.py`

**Step 1: Write test for missing sidecar data**

Add to `tests/unit/modules/test_transform.py`:

```python
def test_transform_module_handles_missing_sidecar():
    """TransformModule passes through items without sidecar data."""
    sidecar_data = {
        "item-001": {"properties": {"custom": "value"}}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sidecar_data, f)
        temp_path = f.name
    
    try:
        module = TransformModule({"input_file": temp_path})
        context = MockWorkflowContext.create()
        
        item = VALID_ITEM.copy()
        item["id"] = "missing-item"  # Not in sidecar
        
        result = module.modify(item, context)
        
        # Item should pass through unchanged
        assert result["id"] == "missing-item"
        assert "custom" not in result.get("properties", {})
    finally:
        import os
        os.unlink(temp_path)
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/unit/modules/test_transform.py::test_transform_module_handles_missing_sidecar -v`  
Expected: PASS (already handled in modify method)

**Step 3: Commit**

```bash
git add tests/unit/modules/test_transform.py
git commit -m "test(modules): verify missing sidecar handling"
```

---

### Task 34: Transform Module - Data Path Extraction

**Files:**
- Modify: `tests/unit/modules/test_transform.py`
- Modify: `src/stac_manager/modules/transform.py`

**Step 1: Write test for data_path extraction**

Add to `tests/unit/modules/test_transform.py`:

```python
def test_transform_module_data_path_extraction():
    """TransformModule extracts nested data using data_path."""
    # Wrapped sidecar structure
    wrapped_data = {
        "response": {
            "results": [
                {"id": "item-001", "custom_field": "value1"},
                {"id": "item-002", "custom_field": "value2"}
            ]
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(wrapped_data, f)
        temp_path = f.name
    
    try:
        module = TransformModule({
            "input_file": temp_path,
            "data_path": "response.results"
        })
        
        assert "item-001" in module.sidecar_index
        assert module.sidecar_index["item-001"]["custom_field"] == "value1"
    finally:
        import os
        os.unlink(temp_path)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_transform.py::test_transform_module_data_path_extraction -v`  
Expected: FAIL (data_path not implemented)

**Step 3: Implement data_path extraction**

Update `__init__` in `src/stac_manager/modules/transform.py`:

```python
"""Transform Module - Sidecar data enrichment."""
import json
from pathlib import Path
import jmespath
from stac_manager.modules.config import TransformConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import ConfigurationError
from stac_manager.utils.field_ops import deep_merge


class TransformModule:
    """Enriches items with sidecar data."""
    
    def __init__(self, config: dict) -> None:
        """Initialize and load sidecar file."""
        self.config = TransformConfig(**config)
        self.sidecar_index: dict[str, dict] = {}
        
        # Load sidecar file
        if self.config.input_file:
            file_path = Path(self.config.input_file)
            if not file_path.exists():
                raise ConfigurationError(f"input_file not found: {self.config.input_file}")
            
            with open(file_path, 'r') as f:
                sidecar_data = json.load(f)
            
            # Apply data_path if specified
            if self.config.data_path:
                sidecar_data = jmespath.search(self.config.data_path, sidecar_data)
                if sidecar_data is None:
                    raise ConfigurationError(f"data_path '{self.config.data_path}' returned no results")
            
            # Build index
            if isinstance(sidecar_data, dict):
                self.sidecar_index = sidecar_data
            elif isinstance(sidecar_data, list):
                for record in sidecar_data:
                    record_id = jmespath.search(self.config.sidecar_id_path, record)
                    if record_id:
                        self.sidecar_index[record_id] = record
            else:
                raise ConfigurationError("input_file must be JSON dict or list")
    
    def modify(self, item: dict, context: WorkflowContext) -> dict:
        """
        Enrich item with sidecar data.
        
        Args:
            item: STAC item dict
            context: Workflow context
        
        Returns:
            Enriched item
        """
        item_id = item.get("id")
        if not item_id or item_id not in self.sidecar_index:
            return item
        
        # Get sidecar data for this item
        sidecar_record = self.sidecar_index[item_id]
        
        # Merge based on strategy
        if self.config.strategy == "merge":
            item = deep_merge(item, sidecar_record, strategy='overwrite')
        elif self.config.strategy == "update":
            item = deep_merge(item, sidecar_record, strategy='update_only')
        
        return item
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/modules/test_transform.py -v`  
Expected: All PASS

**Step 5: Commit**

```bash
git add src/stac_manager/modules/transform.py tests/unit/modules/test_transform.py
git commit -m "feat(modules): add data_path extraction to TransformModule"
```

---

### Task 35: Transform Module - Protocol Compliance & Integration

**Files:**
- Modify: `tests/unit/modules/test_transform.py`
- Modify: `src/stac_manager/modules/__init__.py`

**Step 1: Write protocol compliance test**

Add to `tests/unit/modules/test_transform.py`:

```python
from stac_manager.protocols import Modifier


def test_transform_module_implements_modifier_protocol():
    """TransformModule implements Modifier protocol."""
    sidecar_data = {"item-001": {"properties": {"custom": "value"}}}
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sidecar_data, f)
        temp_path = f.name
    
    try:
        module = TransformModule({"input_file": temp_path})
        assert isinstance(module, Modifier)
    finally:
        import os
        os.unlink(temp_path)
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/unit/modules/test_transform.py::test_transform_module_implements_modifier_protocol -v`  
Expected: PASS (already complies)

**Step 3: Add module exports**

Update `src/stac_manager/modules/__init__.py`:

```python
"""Pipeline module implementations."""
from stac_manager.modules.seed import SeedModule
from stac_manager.modules.update import UpdateModule
from stac_manager.modules.validate import ValidateModule
from stac_manager.modules.extension import ExtensionModule
from stac_manager.modules.transform import TransformModule

__all__ = [
    'SeedModule',
    'UpdateModule',
    'ValidateModule',
    'ExtensionModule',
    'TransformModule',
]
```

**Step 4: Run full module test suite**

Run: `pytest tests/unit/modules/ -v`  
Expected: All PASS (all 5 modules)

**Step 5: Commit**

```bash
git add src/stac_manager/modules/__init__.py tests/unit/modules/test_transform.py
git commit -m "feat(modules): complete TransformModule with protocol compliance"
```

---

## Part 2 Summary & Verification

### Completed Tasks: 18-35

**Phase 4: Validate Module** ✅
- Task 18: Basic STAC validation with stac-validator
- Task 19: Strict vs permissive mode (raise vs collect)
- Task 20: Extension schema support
- Task 21: Protocol compliance & module exports

**Phase 5: Extension Module** ✅
- Task 22: Schema fetching with HTTP requests
- Task 23: Template building from simple properties
- Task 24: oneOf schema variant detection (STAC Item heuristic)
- Task 25: User defaults overlay on template
- Task 26: Item tagging (stac_extensions) and merging
- Task 27: Protocol compliance & module exports

**Phase 6: Transform Module** ✅
- Task 28: JSON sidecar file loading
- Task 29: Dict sidecar indexing (keys as IDs)
- Task 30: List sidecar indexing with JMESPath extraction
- Task 31: Basic item enrichment with merge
- Task 32: Update strategy testing (update_only)
- Task 33: Missing item handling (pass-through)
- Task 34: data_path JMESPath extraction for nested structures
- Task 35: Protocol compliance & module exports

### Files Created

**Production Code:**
- `src/stac_manager/modules/validate.py`
- `src/stac_manager/modules/extension.py`
- `src/stac_manager/modules/transform.py`

**Test Code:**
- `tests/unit/modules/test_validate.py`
- `tests/unit/modules/test_extension.py`
- `tests/unit/modules/test_transform.py`

**Updated:**
- `src/stac_manager/modules/__init__.py` (added ValidateModule, ExtensionModule, TransformModule exports)

### Verification Commands

**Run all Part 2 tests:**
```bash
pytest tests/unit/modules/test_validate.py tests/unit/modules/test_extension.py tests/unit/modules/test_transform.py -v
```

**Expected**: All 18 tasks' tests passing

**Run complete module suite (Parts 1 + 2):**
```bash
pytest tests/unit/modules/ -v
```

**Expected**: All modules passing (Seed, Update, Validate, Extension, Transform)

**Coverage check:**
```bash
pytest tests/unit/modules/ --cov=src/stac_manager/modules --cov-report=term-missing
```

**Expected**: ≥90% coverage

---

## Key Patterns Applied

**From Part 1 Learnings:**
- ✅ Dot-notation for patch files and field mappings
- ✅ `deep_merge` strategies: `keep_existing`, `overwrite`, `update_only`
- ✅ Protocol compliance: `assert isinstance(module, Protocol)`
- ✅ Config validation: Pydantic fail-fast (Tier 1) on init
- ✅ Error handling: Native exceptions → DataProcessingError (Tier 2)
- ✅ JMESPath for field extraction and querying

**New Patterns in Part 2:**
- ✅ Schema fetching with `requests` library
- ✅ JSON Schema parsing for template building
- ✅ oneOf variant detection for STAC Items
- ✅ Sidecar indexing for O(1) lookup performance
- ✅ Strategy-based merging (enrichment vs update-only)

---

## Next Steps

**Part 2 is complete and ready for execution!**

Before proceeding to Part 3, you can:

1. **Execute Part 2** using the `executing-plans` skill
2. **Review Part 2** for any adjustments
3. **Return here** after completion for Part 3 expansion

**Part 3 will cover:**

### Part 3: I/O & Integration (Tasks 36-56)
- **IngestModule**: API/File fetching with parallelism and rate limiting
- **OutputModule**: JSON/Parquet output with atomic writes
- **Integration Tests**: End-to-end module interoperability validation
- **Verification**: Complete Phase 2 testing and documentation

**Total remaining**: 21 tasks to complete Phase 2

