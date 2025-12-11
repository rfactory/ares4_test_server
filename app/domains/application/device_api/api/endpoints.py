# server2/app/domains/application/device_api/api/endpoints.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Union, Literal

# Dependencies
from app.dependencies import get_db, get_current_user

# Models
from app.models.objects.user import User as DBUser
from app.domains.services.device_management.schemas.device import Device as DeviceSchema

# Schemas from other domains
from app.domains.application.device_provisioning.schemas.provisioning import DeviceClaimRequest
from app.domains.services.device_management.schemas.device import DeviceUpdate
from app.domains.services.device_access_management.services.device_access_management_service import PersonalDeviceResponse # 개인 컨텍스트 응답 스키마

# Inter-domain providers / Application service providers
from app.domains.application.device_provisioning.services.device_provisioning_service import device_provisioning_service
from app.domains.inter_domain.device_access_management.providers import device_access_management_providers
from app.domains.inter_domain.device_management.providers import device_management_providers

router = APIRouter()

@router.post("/provision", response_model=DeviceSchema)
def provision_device(
    *,
    db: Session = Depends(get_db),
    claim_in: DeviceClaimRequest,
    current_user: DBUser = Depends(get_current_user),
):
    """
    Provision a new device. This is a high-level workflow.
    """
    return device_provisioning_service.provision_new_device(db=db, claim_in=claim_in, request_user=current_user)

@router.get("/", response_model=List[Union[DeviceSchema, PersonalDeviceResponse]])
def list_devices(
    *,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user),
    active_context: Union[Literal['personal', 'global'], int] = Query(..., description="The active context ('personal', 'global', or an organization ID)"),
    nicknames: Optional[List[str]] = Query(None, description="Optional list of nicknames to filter by. Only effective within the active context."),
    skip: int = Query(0, description="Number of items to skip"),
    limit: int = Query(100, description="Maximum number of items to return")
) -> List[Union[Device, PersonalDeviceResponse]]:
    """
    Retrieve a list of devices based on the active context and optional nickname filtering.
    The response model changes based on the active_context.
    """
    return device_access_management_providers.get_visible_device_list(
        db=db, request_user=current_user, active_context=active_context, nicknames=nicknames, skip=skip, limit=limit
    )

@router.get("/{device_id}", response_model=DeviceSchema)
def read_device(
    *,
    db: Session = Depends(get_db),
    device_id: int,
    current_user: DBUser = Depends(get_current_user),
    active_context: Union[Literal['personal', 'global'], int] = Query(..., description="The active context ('personal', 'global', or an organization ID)")
):
    """
    Get a specific device by ID. Access is checked within the service layer based on context.
    """
    return device_access_management_providers.get_device_if_user_has_read_access(
        db=db, device_id=device_id, request_user=current_user, active_context=active_context
    )

@router.put("/{device_id}", response_model=DeviceSchema)
def update_device(
    *,
    db: Session = Depends(get_db),
    device_id: int,
    device_in: DeviceUpdate,
    current_user: DBUser = Depends(get_current_user),
    active_context: Union[Literal['personal', 'global'], int] = Query(..., description="The active context ('personal', 'global', or an organization ID)")
):
    """
    Update a device. Access is checked within the service layer based on context.
    """
    # First, verify user has update access and get the device object
    device = device_access_management_providers.get_device_if_user_has_update_access(
        db=db, device_id=device_id, request_user=current_user, active_context=active_context
    )
    # Then, perform the update using the core management service
    return device_management_providers.update_device(db=db, device_id=device.id, obj_in=device_in)

@router.delete("/{device_id}", response_model=DeviceSchema)
def delete_device(
    *,
    db: Session = Depends(get_db),
    device_id: int,
    current_user: DBUser = Depends(get_current_user),
    active_context: Union[Literal['personal', 'global'], int] = Query(..., description="The active context ('personal', 'global', or an organization ID)")
):
    """
    Deletes (soft-deletes) a device. Access is checked within the service layer based on context.
    """
    # First, verify user has delete access
    device = device_access_management_providers.get_device_if_user_has_delete_access(
        db=db, device_id=device_id, request_user=current_user, active_context=active_context
    )
    # Then, perform the delete using the core management service
    return device_management_providers.delete_device(db=db, device_id=device.id)
