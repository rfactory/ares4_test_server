from sqlalchemy.orm import Session
from typing import List
from app.models.relationships.device_component_pin_mapping import DeviceComponentPinMapping, PinStatusEnum

class CRUDPinMappingQuery:
    """[Laborer] 핀 매핑 조회 CRUD: DB 읽기 작업만 전담합니다."""

    def get_by_device(self, db: Session, *, device_id: int) -> List[DeviceComponentPinMapping]:
        """특정 장치에 할당된 모든 핀 매핑 정보를 가져옵니다. (고장난 핀 포함)"""
        return db.query(DeviceComponentPinMapping).filter(
            DeviceComponentPinMapping.device_id == device_id
        ).all()

    def get_active_by_device(self, db: Session, *, device_id: int) -> List[DeviceComponentPinMapping]:
        """
        현재 정상 작동 중(ACTIVE)인 핀 매핑 정보만 가져옵니다.
        (부팅 시 라즈베리파이는 이 정보만 가져갑니다.)
        """
        return db.query(DeviceComponentPinMapping).filter(
            DeviceComponentPinMapping.device_id == device_id,
            # [수정] is_active 삭제 -> status가 ACTIVE인 것만 조회
            DeviceComponentPinMapping.status == PinStatusEnum.ACTIVE
        ).all()

pin_mapping_crud_query = CRUDPinMappingQuery()