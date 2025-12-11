# crud/device_query_crud.py
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from app.models.objects.device import Device
from ..schemas.device_query import DeviceQuery

class CRUDDeviceQuery:
    def get(self, db: Session, *, id: int) -> Optional[Device]:
        """ID로 활성 장치를 조회합니다."""
        return db.query(Device).filter(Device.id == id, Device.is_active == True).first()

    def get_multi(self, db: Session, *, query_params: DeviceQuery) -> List[Device]:
        """
        DeviceQuery 스키마를 기반으로 동적으로 쿼리하여 장치 목록을 조회합니다.
        """
        query = db.query(Device)

        # 동적 필터링
        if query_params.id is not None:
            query = query.filter(Device.id == query_params.id)
        if query_params.cpu_serial:
            query = query.filter(Device.cpu_serial == query_params.cpu_serial)
        if query_params.current_uuid:
            query = query.filter(Device.current_uuid == query_params.current_uuid)
        if query_params.hardware_blueprint_id:
            query = query.filter(Device.hardware_blueprint_id == query_params.hardware_blueprint_id)
        if query_params.visibility_status:
            query = query.filter(Device.visibility_status == query_params.visibility_status)
        if query_params.status:
            query = query.filter(Device.status == query_params.status)
        if query_params.is_active is not None:
            query = query.filter(Device.is_active == query_params.is_active)

        # 정렬 (기본값: 생성일 내림차순)
        query = query.order_by(Device.created_at.desc())

        return query.offset(query_params.skip).limit(query_params.limit).all()

device_query_crud = CRUDDeviceQuery()
