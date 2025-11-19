from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from uuid import UUID

from app.models.objects.device import Device
from app.models.objects.user import User as DBUser
from app.models.relationships.user_device import UserDevice
from app.domains.devices.schemas import DeviceCreate, DeviceUpdate
from app.core.authorization import authorization_service
from app.core.exceptions import PermissionDeniedError, NotFoundError

class CRUDDevice:
    def get(
        self, db: Session, *, id: int, request_user: DBUser
    ) -> Device:
        """Get a single device by ID, with authorization checks."""
        db_device = db.query(Device).filter(Device.id == id).first()
        if not db_device:
            raise NotFoundError(resource_name="Device", resource_id=str(id))

        # 1. Check for global "read all" permission (replaces is_superuser)
        # This permission will be granted to roles like Prime_Admin.
        if authorization_service.check_user_permission(db, user=request_user, permission_name="device:read_all"):
            return db_device

        # 2. Check for corporate device access
        if db_device.organization_id:
            if authorization_service.check_user_permission(
                db, user=request_user, permission_name="device:read", organization_id=db_device.organization_id
            ):
                return db_device
        
        # 3. Check for personal device ownership
        else:
            is_owner = db.query(UserDevice).filter(
                UserDevice.device_id == db_device.id, 
                UserDevice.user_id == request_user.id
            ).first() is not None
            if is_owner:
                return db_device
        
        # 4. If no permissions match, deny access
        raise PermissionDeniedError(f"User does not have permission to access device {id}")

    def get_by_cpu_serial(self, db: Session, cpu_serial: str) -> Optional[Device]:
        return db.query(Device).filter(Device.cpu_serial == cpu_serial).first()

    def get_by_current_uuid(self, db: Session, current_uuid: UUID) -> Optional[Device]:
        return db.query(Device).filter(Device.current_uuid == current_uuid).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100, request_user: DBUser
    ) -> List[Device]:
        """Get multiple devices, filtered by user's permissions."""
        # 1. Check for global "read all" permission (replaces is_superuser)
        if authorization_service.check_user_permission(db, user=request_user, permission_name="device:read_all"):
            return db.query(Device).offset(skip).limit(limit).all()

        # 2. If no global permission, gather devices based on specific org roles and personal ownership
        allowed_org_ids = []
        for assignment in request_user.user_role_assignments:
            if assignment.organization_id and authorization_service.check_user_permission(
                db, user=request_user, permission_name="device:read", organization_id=assignment.organization_id
            ):
                allowed_org_ids.append(assignment.organization_id)
        
        # Get personal devices
        personal_devices_query = db.query(Device).join(UserDevice).filter(
            UserDevice.user_id == request_user.id,
            Device.organization_id == None
        )

        # Get corporate devices in allowed orgs
        corporate_devices_query = db.query(Device).filter(Device.organization_id.in_(allowed_org_ids))

        # Combine and execute
        # This requires a more sophisticated union query, which can be complex.
        # For now, we will fetch separately and combine. This is not efficient for pagination.
        # TODO: Refactor to a more efficient single query.
        personal_devices = personal_devices_query.all()
        corporate_devices = corporate_devices_query.all()
        
        all_devices = personal_devices + corporate_devices
        return all_devices[skip : skip + limit]

    def create(
        self, db: Session, *, obj_in: DeviceCreate, request_user: DBUser
    ) -> Device:
        """
        Creates a device, either as a personal or corporate device, with authorization.
        For simplicity, this example assumes 'obj_in' contains organization_id for corporate, or it's None for personal.
        """
        # Case 1: Corporate device creation
        if obj_in.organization_id:
            if not authorization_service.check_user_permission(
                db, user=request_user, permission_name="device:create", organization_id=obj_in.organization_id
            ):
                raise PermissionDeniedError(f"User does not have 'device:create' permission in organization {obj_in.organization_id}")
            
            db_obj = Device(**obj_in.dict())
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        
        # Case 2: Personal device creation
        else:
            # Any authenticated user can create a personal device
            db_obj = Device(**obj_in.dict(exclude={'organization_id'})) # Ensure org_id is not set
            db_obj.organization_id = None
            db.add(db_obj)
            db.flush() # Flush to get the ID for the association

            # Create the ownership link
            ownership_link = UserDevice(user_id=request_user.id, device_id=db_obj.id, role='owner')
            db.add(ownership_link)
            db.commit()
            db.refresh(db_obj)
            return db_obj

    def update(
        self, db: Session, *, id: int, obj_in: DeviceUpdate, request_user: DBUser
    ) -> Device:
        """Update a device, with authorization checks."""
        db_device = self.get(db, id=id, request_user=request_user) # The get() method already performs the necessary auth checks
        
        # The get() method will raise an error if the user doesn't have read access.
        # We need an explicit 'update' permission check here as well.
        
        # Case 1: Corporate device
        if db_device.organization_id:
             if not authorization_service.check_user_permission(
                db, user=request_user, permission_name="device:update", organization_id=db_device.organization_id
            ):
                raise PermissionDeniedError(f"User does not have 'device:update' permission in organization {db_device.organization_id}")
        # Case 2: Personal device ownership is already confirmed by self.get()

        # Proceed with update
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_device, field, value)
        
        db.add(db_device)
        db.commit()
        db.refresh(db_device)
        return db_device

    def delete(
        self, db: Session, *, id: int, request_user: DBUser
    ) -> Device:
        """Delete a device, with authorization checks."""
        db_device = self.get(db, id=id, request_user=request_user) # Auth check is performed here

        # Explicit check for 'delete' permission
        if db_device.organization_id:
            if not authorization_service.check_user_permission(
                db, user=request_user, permission_name="device:delete", organization_id=db_device.organization_id
            ):
                raise PermissionDeniedError(f"User does not have 'device:delete' permission in organization {db_device.organization_id}")
        # Personal device ownership already confirmed by self.get()

        db.delete(db_device)
        db.commit()
        return db_device

device_crud = CRUDDevice()
