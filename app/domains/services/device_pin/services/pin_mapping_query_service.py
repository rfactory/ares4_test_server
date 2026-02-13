from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..crud.pin_mapping_query_crud import pin_mapping_crud_query
from app.models.relationships.device_component_pin_mapping import DeviceComponentPinMapping

class PinMappingQueryService:
    """[Laborer] 핀 매핑 조회 서비스: 기기나 UI가 요청한 배선 정보를 제공합니다."""

    def get_actual_mappings(self, db: Session, *, device_id: int) -> List[DeviceComponentPinMapping]:
        """
        장치의 현재 실제 핀 배선 상태를 조회합니다.
        (관리자 화면용: 고장난 핀이나 비활성 핀도 모두 포함하여 보여줍니다.)
        """
        return pin_mapping_crud_query.get_by_device(db, device_id=device_id)

    def get_boot_config_mappings(self, db: Session, *, device_id: int) -> Dict[str, Dict[str, Any]]:
        """
        [P4.1] 라즈베리파이 부팅 시 필요한 핀 설정 맵을 생성합니다.
        (기기가 이해하기 쉬운 딕셔너리 형태로 가공합니다.)
        
        Return Example:
        {
            "PUMP_MAIN": {"pin_number": 17, "mode": "OUTPUT"},
            "TEMP_SENSOR": {"pin_number": 4, "mode": "INPUT"}
        }
        """
        # CRUD를 통해 'ACTIVE' 상태인 핀들만 가져옵니다.
        mappings = pin_mapping_crud_query.get_active_by_device(db, device_id=device_id)
        
        # 기기가 바로 로직에 투입할 수 있도록 핀 이름을 키(Key)로 하는 맵 반환
        return {
            m.pin_name: {
                "pin_number": m.pin_number, 
                "mode": m.pin_mode
            } 
            for m in mappings
        }

pin_mapping_query_service = PinMappingQueryService()