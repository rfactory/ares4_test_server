from sqlalchemy.orm import Session
from app.domains.services.device_pin.services.pin_mapping_command_service import pin_mapping_command_service

class PinMappingCommandProvider:
    """[Inter-Domain] 핀 매핑 변경 전용 공급자"""

    def initialize_device_pins(self, db: Session, *, device_id: int):
        """기기 등록 시 설계도 정보를 실제 핀 테이블로 복제합니다."""
        return pin_mapping_command_service.clone_from_blueprint(db, device_id=device_id)

    def update_actual_pin(self, db: Session, *, mapping_id: int, new_pin: int):
        """Flutter/Web 요청에 따른 실제 배선 번호 수정"""
        return pin_mapping_command_service.update_pin(db, mapping_id=mapping_id, new_pin=new_pin)

pin_mapping_command_provider = PinMappingCommandProvider()