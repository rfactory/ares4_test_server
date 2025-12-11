# server2/app/domains/services/device_provisioning/services/device_provisioning_service.py

from sqlalchemy.orm import Session
import uuid

# Schemas
from ..schemas.provisioning import DeviceClaimRequest
from app.domains.services.device_management.schemas.device import DeviceCreate
from app.domains.services.device_access_management.schemas.user_device import UserDeviceCreate

# Models
from app.models.objects.device import Device
from app.models.objects.user import User as DBUser

# Exceptions
from app.core.exceptions import PermissionDeniedError

# Inter-domain providers
from app.domains.inter_domain.user_authorization.providers import user_authorization_providers
from app.domains.inter_domain.device_management.providers import device_management_providers
from app.domains.inter_domain.device_access_management.providers import device_access_management_providers
from app.domains.inter_domain.audit.providers import audit_providers

class DeviceProvisioningService:
    def provision_new_device(self, db: Session, *, claim_in: DeviceClaimRequest, request_user: DBUser) -> Device:
        """
        Orchestrates the entire device provisioning and claiming workflow.
        """
        # 1. --- Authorization Check ---
        # For now, let's assume a general permission. This could be more granular.
        if not user_authorization_providers.check_user_permission(db, user=request_user, permission_name="device:provision"):
            raise PermissionDeniedError("User does not have permission to provision new devices.")
            
        # 2. --- Validation (Pre-checks) ---
        # TODO: Get hardware blueprint based on claim_in.hardware_blueprint_version
        # For now, using a placeholder.
        hardware_blueprint_id = 1 

        # 3. --- Create Device (Core) --- 
        # The orchestrator is responsible for creating the full `DeviceCreate` object
        device_create_obj = DeviceCreate(
            cpu_serial=claim_in.cpu_serial,
            current_uuid=uuid.uuid4(),
            hardware_blueprint_id=hardware_blueprint_id,
            # organization_id can be added here if needed
        )
        new_device = device_management_providers.create_device(db, obj_in=device_create_obj)

        # 4. --- Link Ownership ---
        link_obj = UserDeviceCreate(
            user_id=request_user.id,
            device_id=new_device.id,
            role='owner'
        )
        device_access_management_providers.link_device_to_user(db, link_in=link_obj, actor_user=request_user)

        # 5. --- Audit Log ---
        audit_providers.log(
            db=db,
            event_type="DEVICE_PROVISIONED",
            description=f"New device '{new_device.cpu_serial}' was provisioned by user {request_user.username}.",
            actor_user=request_user,
            target_device=new_device
        )
        
        return new_device

device_provisioning_service = DeviceProvisioningService()
