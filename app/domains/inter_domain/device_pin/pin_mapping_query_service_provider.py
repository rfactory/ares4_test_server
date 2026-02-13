from sqlalchemy.orm import Session
from app.domains.services.device_pin.services.pin_mapping_query_service import pin_mapping_query_service

class PinMappingQueryProvider:
    """[Inter-Domain] 핀 매핑 조회 전용 공급자"""
    
    def get_actual_mappings(self, db: Session, *, device_id: int):
        """
        [For UI/Admin] 장치의 실제 핀 매핑 전체 리스트 제공 
        (고장난 핀 포함, 수정 시 ID 참조용)
        """
        return pin_mapping_query_service.get_actual_mappings(db, device_id=device_id)

    def get_boot_config(self, db: Session, *, device_id: int):
        """
        [For Device] 라즈베리파이 부팅 시 필요한 핀 매핑 딕셔너리 제공
        (ACTIVE 상태인 핀만 포함)
        """
        return pin_mapping_query_service.get_boot_config_mappings(db, device_id=device_id)

pin_mapping_query_provider = PinMappingQueryProvider()