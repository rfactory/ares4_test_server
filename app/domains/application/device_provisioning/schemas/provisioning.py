from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class DeviceClaimRequest(BaseModel):
    cpu_serial: str
    hardware_blueprint_version: str

class DeviceCredentials(BaseModel):
    user_email: str
    shared_secret: str
    device_certificate: Optional[str] = None
    device_private_key: Optional[str] = None
    ca_certificate: Optional[str] = None
    device_uuid: UUID
