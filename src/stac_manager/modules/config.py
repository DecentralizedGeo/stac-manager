"""Pydantic configuration models for pipeline modules."""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any, List, Union, Literal


class SeedConfig(BaseModel):
    """Configuration for SeedModule."""
    items: Optional[List[Union[str, Dict[str, Any]]]] = None
    source_file: Optional[str] = None
    defaults: Optional[Dict[str, Any]] = None


class UpdateConfig(BaseModel):
    """Configuration for UpdateModule."""
    updates: Optional[Dict[str, Any]] = None
    removes: Optional[List[str]] = None
    patch_file: Optional[str] = None
    mode: Literal['merge', 'replace', 'update_only'] = 'merge'
    create_missing_paths: bool = True
    auto_update_timestamp: bool = True


class ValidateConfig(BaseModel):
    """Configuration for ValidateModule."""
    strict: bool = False
    extension_schemas: List[HttpUrl] = Field(default_factory=list)


class ExtensionConfig(BaseModel):
    """Configuration for ExtensionModule."""
    schema_uri: str
    defaults: Optional[Dict[str, Any]] = None
    validate_extension: bool = False
    required_fields_only: bool = False


class TransformConfig(BaseModel):
    """Configuration for TransformModule."""
    input_file: Optional[str] = None
    strategy: Literal['merge', 'update'] = 'merge'
    sidecar_id_path: str = "id"
    data_path: Optional[str] = None
    field_mapping: Optional[Dict[str, str]] = None
    handle_missing: Literal['ignore', 'warn', 'error'] = 'ignore'
    schema_file: Optional[str] = None
    schema_mapping: Optional[Dict[str, Any]] = Field(alias='schema', default=None)


class IngestConfig(BaseModel):
    """Configuration for IngestModule."""
    mode: Literal["file", "api"] = Field(description="Ingestion mode")
    source: str = Field(description="File/directory path (file mode) or API catalog URL (api mode)")
    source_type: Optional[Literal["auto", "file", "items_directory", "collection"]] = Field(
        default="auto",
        description="Source type: 'auto' (auto-detect), 'file' (single JSON/Parquet), 'items_directory' (directory of items), 'collection' (collection root or collection.json)"
    )
    format: Optional[Literal["json", "parquet"]] = Field(default=None, description="File format override (auto-detected if not specified)")
    collection_id: Optional[str] = Field(default=None, description="Single collection to fetch (API mode). If not set, uses context.data['collection_id']")
    bbox: Optional[List[float]] = Field(default=None, description="Bounding box filter")
    datetime: Optional[str] = Field(default=None, description="Datetime filter")
    query: Optional[Dict[str, Any]] = Field(default=None, description="CQL query")
    limit: Optional[int] = Field(default=100, description="Items per page")
    max_items: Optional[int] = Field(default=None, description="Maximum items to fetch")


class OutputConfig(BaseModel):
    """Configuration for OutputModule."""
    format: Literal["json", "parquet"] = Field(description="Output format")
    base_dir: str = Field(description="Base output directory")
    buffer_size: int = Field(default=1000, description="Items to buffer before flushing")
    base_url: Optional[str] = Field(default=None, description="Base URL for item links (reserved for future use)")
