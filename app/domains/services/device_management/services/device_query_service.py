# services/device_query_service.py
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID # UUID 타입 힌팅을 위해 추가

from ..crud.device_query_crud import device_query_crud
from ..schemas.device_query import DeviceQuery, DeviceRead

class DeviceManagementQueryService:
    def get_devices(self, db: Session, *, query_params: DeviceQuery) -> List[DeviceRead]:
        """DeviceQuery 스키마를 사용하여 장치 목록을 동적으로 조회합니다."""
        db_devices = device_query_crud.get_multi(db, query_params=query_params)
        # Pydantic v2에서는 .from_orm() 대신 .model_validate()를 사용할 수 있습니다.
        return [DeviceRead.model_validate(device) for device in db_devices]

    def get_device_by_id(self, db: Session, *, id: int) -> Optional[DeviceRead]:
        """ID로 단일 장치를 조회하는, 매우 일반적인 조회 기능입니다."""
        db_device = device_query_crud.get(db, id=id)
        return DeviceRead.model_validate(db_device) if db_device else None

    def get_device_by_uuid(self, db: Session, *, current_uuid: UUID) -> Optional[DeviceRead]:
        """UUID로 단일 장치를 조회합니다."""
        query_params = DeviceQuery(current_uuid=current_uuid)
        db_device = device_query_crud.get_multi(db, query_params=query_params)
        # get_multi는 리스트를 반환하므로, 첫 번째 항목을 가져옵니다. (UUID는 Unique하므로 최대 1개)
        return DeviceRead.model_validate(db_device[0]) if db_device else None

device_management_query_service = DeviceManagementQueryService()
