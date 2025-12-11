from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from app.models.events_logs.telemetry_data import TelemetryData as DBTelemetryData
from app.models.events_logs.telemetry_metadata import TelemetryMetadata as DBTelemetryMetadata
from ..schemas import TelemetryDataCreate # TelemetryDataUpdate is removed
from app.models.objects.user import User as DBUser
from app.domains.devices.crud import device_crud
from app.core.exceptions import PermissionDeniedError, NotFoundError

class CRUDTelemetryData:
    def _authorize_device_access(self, db: Session, device_id: int, request_user: DBUser) -> None:
        """Helper function to authorize read access to a device's telemetry by reusing device_crud."""
        try:
            # This call will handle all RBAC, ownership, and global admin checks for the device.
            device_crud.get(db, id=device_id, request_user=request_user)
        except (NotFoundError, PermissionDeniedError) as e:
            # If device_crud.get fails, the user does not have rights to this device's telemetry.
            raise PermissionDeniedError(f"User does not have access to telemetry for device ID {device_id}") from e

    def create_telemetry_data(self, db: Session, *, telemetry_data: TelemetryDataCreate, request_user: DBUser) -> DBTelemetryData:
        # Before creating telemetry, check if user has rights to the device.
        self._authorize_device_access(db, device_id=telemetry_data.device_id, request_user=request_user)
        
        db_telemetry = DBTelemetryData(**telemetry_data.dict(exclude={"metadata_items"}))
        db.add(db_telemetry)
        db.flush() # Flush to get db_telemetry.id for metadata

        if telemetry_data.metadata_items:
            for meta_item in telemetry_data.metadata_items:
                db_metadata = DBTelemetryMetadata(
                    telemetry_data_id=db_telemetry.id, **meta_item.dict()
                )
                db.add(db_metadata)
        
        db.commit()
        db.refresh(db_telemetry)
        return db_telemetry

    def get_telemetry_data(self, db: Session, *, telemetry_data_id: int, request_user: DBUser) -> DBTelemetryData:
        db_telemetry = db.query(DBTelemetryData).options(
            joinedload(DBTelemetryData.metadata_items)
        ).filter(DBTelemetryData.id == telemetry_data_id).first()

        if not db_telemetry:
            raise NotFoundError(resource_name="TelemetryData", resource_id=str(telemetry_data_id))

        # Check for access rights to the device linked to this telemetry record.
        self._authorize_device_access(db, device_id=db_telemetry.device_id, request_user=request_user)
        return db_telemetry

    def get_multiple_telemetry_data(
        self,
        db: Session,
        *,
        request_user: DBUser,
        skip: int = 0,
        limit: int = 100,
        device_id: Optional[int] = None,
        metric_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[DBTelemetryData]:
        query = db.query(DBTelemetryData).options(joinedload(DBTelemetryData.device))

        # If a specific device_id is requested, authorize for that single device.
        if device_id:
            self._authorize_device_access(db, device_id=device_id, request_user=request_user)
            query = query.filter(DBTelemetryData.device_id == device_id)
        else:
            # If no specific device is requested, filter by all devices the user has access to.
            accessible_devices = device_crud.get_multi(db, request_user=request_user, limit=10000) # A large limit to get all devices
            accessible_device_ids = [d.id for d in accessible_devices]
            if not accessible_device_ids:
                return [] # Return empty if user has access to no devices
            query = query.filter(DBTelemetryData.device_id.in_(accessible_device_ids))

        if metric_name:
            query = query.filter(DBTelemetryData.metric_name == metric_name)
        if start_time:
            query = query.filter(DBTelemetryData.timestamp >= start_time)
        if end_time:
            query = query.filter(DBTelemetryData.timestamp <= end_time)
        
        return query.offset(skip).limit(limit).all()
    
telemetry_crud = CRUDTelemetryData()
