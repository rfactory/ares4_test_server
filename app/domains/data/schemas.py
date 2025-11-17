from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

# Import SQLAlchemy models from their centralized location
from app.models.events_logs.telemetry_data import TelemetryData as DBTelemetryData
from app.models.events_logs.telemetry_metadata import TelemetryMetadata as DBTelemetryMetadata
from app.models.objects.device import Device as DBDevice # For nested device info

# --- TelemetryMetadata Schemas ---
class MetaValueType(str, Enum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    ENUM = "ENUM"
    JSON = "JSON"

class TelemetryMetadataBase(BaseModel):
    meta_key: str
    meta_value: str # Stored as string, will be cast based on meta_value_type
    meta_value_type: MetaValueType = MetaValueType.STRING
    description: Optional[str] = None

class TelemetryMetadataCreate(TelemetryMetadataBase):
    pass

class TelemetryMetadataResponse(TelemetryMetadataBase):
    id: int
    telemetry_data_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- TelemetryData Schemas ---
class TelemetryDataBase(BaseModel):
    device_id: int
    timestamp: datetime
    metric_name: str
    metric_value: float
    unit: Optional[str] = None

class TelemetryDataCreate(TelemetryDataBase):
    metadata_items: Optional[List[TelemetryMetadataCreate]] = None

class TelemetryDataUpdate(BaseModel):
    timestamp: Optional[datetime] = None
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    unit: Optional[str] = None
    # Metadata updates might be handled separately or as a full replacement

class DeviceInfo(BaseModel):
    id: int
    cpu_serial: str # Changed from device_name

    model_config = ConfigDict(from_attributes=True)

class TelemetryDataResponse(TelemetryDataBase):
    id: int
    created_at: datetime
    updated_at: datetime
    metadata_items: List[TelemetryMetadataResponse] = []
    device: Optional[DeviceInfo] = None # Nested device info

    model_config = ConfigDict(from_attributes=True)

# --- Combined Schemas for API Input/Output ---
class TelemetryDataWithMetadata(TelemetryDataBase):
    metadata_items: List[TelemetryMetadataCreate]

class TelemetryDataFullResponse(TelemetryDataResponse):
    # This can be used if a more comprehensive response is needed,
    # potentially including more detailed device info or other related data.
    pass
