from sqlalchemy.orm import Session, joinedload
from typing import Optional, List

from sqlalchemy.orm import Session, joinedload
from typing import Optional, List

from app.models.relationships.device_component_instance import DeviceComponentInstance

class CRUDDeviceComponentInstanceQuery:
    # 헬퍼 메서드 추가 (내부적으로만 사용)
    def _base_filter(self, db: Session, *, device_id: int, supported_component_id: int):
        return db.query(DeviceComponentInstance).filter(
            DeviceComponentInstance.device_id == device_id,
            DeviceComponentInstance.supported_component_id == supported_component_id,
        )

    def get_any_instance_by_device_and_component_id(
        self, db: Session, *, device_id: int, supported_component_id: int
    ) -> Optional[DeviceComponentInstance]:
        """특정 장치와 부품 ID로 임의의 단일 연결 인스턴스가 존재하는지 확인합니다."""
        # 헬퍼 메서드 사용
        return self._base_filter(
            db, device_id=device_id, supported_component_id=supported_component_id
        ).first()

    def get_by_device_id_and_supported_component_id(
        self, db: Session, *, device_id: int, supported_component_id: int, instance_name: str
    ) -> Optional[DeviceComponentInstance]:
        """특정 장치, 부품 종류, 인스턴스 이름으로 특정 연결 인스턴스를 조회합니다."""
        # 헬퍼 메서드 사용
        return self._base_filter(
            db, device_id=device_id, supported_component_id=supported_component_id
        ).filter(
            DeviceComponentInstance.instance_name == instance_name
        ).first()

    def get_instances_by_device_id(self, db: Session, *, device_id: int) -> List[DeviceComponentInstance]:
        """특정 장치 ID에 연결된 모든 부품 인스턴스를 관련 부품 정보와 함께 조회합니다."""
        return (
            db.query(DeviceComponentInstance)
            .filter(DeviceComponentInstance.device_id == device_id)
            .options(joinedload(DeviceComponentInstance.supported_component))
            .all()
        )

device_component_instance_query_crud = CRUDDeviceComponentInstanceQuery()