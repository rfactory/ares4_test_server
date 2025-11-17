from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.models.objects.device import Device # SQLAlchemy 모델 임포트
from app.domains.devices.schemas import DeviceCreate, DeviceUpdate # Pydantic 스키마 임포트

class CRUDDevice:
    def get(self, db: Session, id: int) -> Optional[Device]:
        return db.query(Device).filter(Device.id == id).first()

    def get_by_cpu_serial(self, db: Session, cpu_serial: str) -> Optional[Device]:
        return db.query(Device).filter(Device.cpu_serial == cpu_serial).first()

    def get_by_current_uuid(self, db: Session, current_uuid: UUID) -> Optional[Device]:
        return db.query(Device).filter(Device.current_uuid == current_uuid).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[Device]:
        return db.query(Device).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: DeviceCreate) -> Device:
        db_obj = Device(
            cpu_serial=obj_in.cpu_serial,
            current_uuid=obj_in.current_uuid,
            hardware_blueprint_id=obj_in.hardware_blueprint_id,
            organization_id=obj_in.organization_id,
            device_certificate_id=obj_in.device_certificate_id,
            ca_certificate_id=obj_in.ca_certificate_id,
            visibility_status=obj_in.visibility_status,
            last_seen_at=obj_in.last_seen_at
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: Device, obj_in: DeviceUpdate) -> Device:
        if obj_in.cpu_serial is not None:
            db_obj.cpu_serial = obj_in.cpu_serial
        if obj_in.current_uuid is not None:
            db_obj.current_uuid = obj_in.current_uuid
        if obj_in.hardware_blueprint_id is not None:
            db_obj.hardware_blueprint_id = obj_in.hardware_blueprint_id
        if obj_in.organization_id is not None:
            db_obj.organization_id = obj_in.organization_id
        if obj_in.device_certificate_id is not None:
            db_obj.device_certificate_id = obj_in.device_certificate_id
        if obj_in.ca_certificate_id is not None:
            db_obj.ca_certificate_id = obj_in.ca_certificate_id
        if obj_in.visibility_status is not None:
            db_obj.visibility_status = obj_in.visibility_status
        if obj_in.last_seen_at is not None:
            db_obj.last_seen_at = obj_in.last_seen_at
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> Optional[Device]:
        obj = db.query(Device).filter(Device.id == id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj

device_crud = CRUDDevice()
