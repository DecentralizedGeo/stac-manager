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
    validate: bool = False
    required_fields_only: bool = False


class TransformConfig(BaseModel):
    """Configuration for TransformModule."""
    input_file: Optional[str] = None
    strategy: Literal['merge', 'update'] = 'merge'
    sidecar_id_path: str = "id"
    data_path: Optional[str] = None
    schema_file: Optional[str] = None
    schema_mapping: Optional[Dict[str, Any]] = Field(alias='schema', default=None)


class IngestFilters(BaseModel):
    """Common filters for STAC API searches."""
    bbox: Optional[List[float]] = None
    datetime: Optional[str] = None
    query: Optional[Dict[str, Any]] = None
    ids: Optional[List[str]] = None


class IngestConfig(BaseModel):
    """Configuration for IngestModule."""
    catalog_url: Optional[str] = None
    collection_id: Optional[str] = None
    source_file: Optional[str] = None
    concurrency: int = Field(default=10, ge=1)
    filters: Optional[IngestFilters] = None


class OutputConfig(BaseModel):
    """Configuration for OutputModule."""
    base_dir: str
    format: Literal['json', 'parquet'] = 'json'
    base_url: Optional[str] = Field(alias='BASE_URL', default=None)
