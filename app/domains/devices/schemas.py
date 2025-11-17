from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

# --- HardwareBlueprint Schemas ---
class HardwareBlueprintBase(BaseModel):
    blueprint_version: str
    blueprint_name: str
    description: Optional[str] = None
    product_line_id: int

class HardwareBlueprintCreate(HardwareBlueprintBase):
    pass

class HardwareBlueprint(HardwareBlueprintBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Certificate Schemas ---
class CertificateBase(BaseModel):
    certificate_name: str
    certificate_content: str

class CertificateCreate(CertificateBase):
    pass

class Certificate(CertificateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Organization Schemas (Simplified for Device context) ---
class OrganizationBase(BaseModel):
    company_name: str
    contact_email: str

class Organization(OrganizationBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Device Schemas ---
class DeviceBase(BaseModel):
    cpu_serial: str
    current_uuid: UUID
    hardware_blueprint_id: int
    organization_id: Optional[int] = None # OrganizationFKMixin
    device_certificate_id: Optional[int] = None # NullableCertificateFKMixin
    ca_certificate_id: Optional[int] = None # NullableCertificateFKMixin
    visibility_status: str = "PRIVATE" # Enum('PRIVATE', 'ORGANIZATION', 'PUBLIC')
    last_seen_at: Optional[datetime] = None

# Properties to receive via API on creation
class DeviceCreate(DeviceBase):
    pass

# Properties to receive via API on update
class DeviceUpdate(BaseModel):
    cpu_serial: Optional[str] = None
    current_uuid: Optional[UUID] = None
    hardware_blueprint_id: Optional[int] = None
    organization_id: Optional[int] = None
    device_certificate_id: Optional[int] = None
    ca_certificate_id: Optional[int] = None
    visibility_status: Optional[str] = None
    last_seen_at: Optional[datetime] = None

# Properties shared by models stored in DB
class DeviceInDBBase(DeviceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Properties to return to client (with relationships)
class Device(DeviceInDBBase):
    hardware_blueprint: HardwareBlueprint
    organization: Optional[Organization] = None
    device_certificate: Optional[Certificate] = None
    ca_certificate: Optional[Certificate] = None
    # Add other relationships as needed, e.g., component_instances: List[DeviceComponentInstance]

# Properties properties stored in DB, but not returned to client
class DeviceInDB(DeviceInDBBase):
    pass

# --- UserDevice Schemas (for linking Users to Devices) ---
class UserDeviceBase(BaseModel):
    user_id: int
    device_id: int
    role: str = "viewer" # e.g., owner, viewer
    nickname: Optional[str] = None

class UserDeviceCreate(UserDeviceBase):
    pass

class UserDevice(UserDeviceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
