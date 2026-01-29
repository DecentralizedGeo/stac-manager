"""Transform Module - Input data enrichment."""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import jmespath
try:
    import pyarrow as pa
    import pyarrow.csv as pacsv
except ImportError:
    pa = None
    pacsv = None

from stac_manager.modules.config import TransformConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import ConfigurationError, DataProcessingError
from stac_manager.utils.field_ops import set_nested_field

logger = logging.getLogger(__name__)


class TransformModule:
    """Enriches items with input data using generic field mapping."""
    
    def __init__(self, config: dict) -> None:
        """Initialize and load input file."""
        self.config = TransformConfig(**config)
        self.input_index: dict[str, dict] = {}
        
        file_path = Path(self.config.input_file)
        if not file_path.exists():
            raise ConfigurationError(f"input_file not found: {self.config.input_file}")
            
        # generic loader dispatch
        if file_path.suffix.lower() == '.csv':
            self._load_csv(file_path)
        else:
            self._load_json(file_path)

    def _load_csv(self, file_path: Path) -> None:
        """Load CSV using pyarrow for type inference."""
        if pa is None:
            raise ConfigurationError("pyarrow is required for CSV support")
            
        join_key = self.config.input_join_key
        
        # Force join key to string to match STAC IDs
        convert_options = pacsv.ConvertOptions(
            column_types={join_key: pa.string()}
        )
        
        try:
            table = pacsv.read_csv(file_path, convert_options=convert_options)
            # efficient conversion to python dicts
            rows = table.to_pylist()
        except Exception as e:
            raise ConfigurationError(f"Failed to load CSV {file_path}: {e}")
            
        # Build index
        for row in rows:
            if join_key in row and row[join_key] is not None:
                self.input_index[str(row[join_key])] = row

    def _load_json(self, file_path: Path) -> None:
        """Load JSON file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except Exception as e:
            raise ConfigurationError(f"Failed to load JSON {file_path}: {e}")
            
        records = data
        
        # Extract list if data_path provided
        if self.config.data_path:
            records = jmespath.search(self.config.data_path, data)
            
        if isinstance(records, dict):
            # Dict: keys are IDs
            self.input_index = {str(k): v for k, v in records.items()}
        elif isinstance(records, list):
            # List: extract IDs using jmespath/key
            join_key = self.config.input_join_key
            for entry in records:
                # Try direct access first (fast), then jmespath
                item_id = entry.get(join_key)
                if item_id is None:
                     item_id = jmespath.search(join_key, entry)
                
                if item_id is not None:
                    self.input_index[str(item_id)] = entry
        else:
            raise ConfigurationError("input_file content must be dict or list (after data_path)")

    def modify(self, item: dict, context: WorkflowContext) -> dict:
        """
        Enrich STAC item with input data.
        
        Args:
            item: STAC item dict
            context: Workflow context
            
        Returns:
            Enriched item dict

        Supports wildcard patterns like `assets.*` and template variables
        like `{item_id}`, `{collection_id}`, `{asset_key}` in field mapping.
        """
        from stac_manager.utils.field_ops import expand_wildcard_paths, set_nested_field,get_nested_field
        
        item_id = item.get("id")
        if not item_id or item_id not in self.input_index:
            if self.config.handle_missing == 'warn':
                context.failure_collector.add(
                    item_id=item_id or "unknown",
                    error="Missing input data",
                    step_id=context.workflow_id
                )
            elif self.config.handle_missing == 'error':
                raise DataProcessingError(f"Missing input data for item {item_id}")
            return item
            
        input_entry = self.input_index[item_id]
        context.logger.debug(f"Enriching item {item_id} from input data")
        
        # Expand wildcards in field_mapping
        context_dict = {
            "item_id": item_id,
            "collection_id": context.data.get("collection_id", "")
        }
        # expand_wildcard_paths returns dict with tuple keys
        expanded_tuples = expand_wildcard_paths(
            self.config.field_mapping,
            item,  # Match wildcards against item structure
            context_dict
        )
        
        # Filter based on strategy
        if self.config.strategy == 'update_existing':
            # Only apply mappings where target path exists in item
            # Use tuple keys to check existence (handles keys with colons correctly)
            
            # Sentinel value pattern: We need to distinguish between:
            # 1. Field doesn't exist → get_nested_field returns default
            # 2. Field exists with None value → get_nested_field returns None
            # Using a unique object() as default lets us detect case #1 with identity check (is)
            # because object() creates a unique instance that can ONLY match via 'is', not '=='
            _MISSING = object()  # Sentinel: guaranteed unique, won't match any real data
            
            final_mapping = {}
            for key_tuple, source_query in expanded_tuples.items():
                # Check if field exists using sentinel
                result = get_nested_field(item, key_tuple, default=_MISSING)
                if result is not _MISSING:
                    # Field exists (even if value is None)
                    target_field = ".".join(key_tuple)
                    final_mapping[target_field] = source_query
                # else: Path doesn't exist, skip it
        else:  # merge strategy
            # Convert all tuple keys to string keys
            final_mapping = {}
            for key_tuple, source_query in expanded_tuples.items():
                target_field = ".".join(key_tuple)
                final_mapping[target_field] = source_query
        
        # Apply field mapping
        for target_field, source_query in final_mapping.items():
            value = self._extract_value(input_entry, source_query)
            
            # If value is None, we skip setting it (to avoid overwriting with Null)
            # Unless we want explicit nulls? Defaulting to skip for now.
            if value is not None:
                set_nested_field(item, target_field, value)
                context.logger.debug(f"Mapped {source_query} -> {target_field}")
        
        return item
        
    def _extract_value(self, record: dict, query: str) -> Any:
        """Extract value using hybrid Simple Key / JMESPath strategy."""
        # Optimized: Try direct key lookup first
        if query in record:
            return record[query]
            
        # Fallback to JMESPath
        return jmespath.search(query, record)
