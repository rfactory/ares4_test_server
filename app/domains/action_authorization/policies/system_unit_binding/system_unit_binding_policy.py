import logging
from sqlalchemy.orm import Session
from typing import Any, Dict

# --- [1] Validators: 판단 로직 위임 ---
from app.domains.inter_domain.validators.system_unit_binding.provider import system_unit_binding_validator_provider

# --- [2] Query Providers: 데이터 조회 위임 ---
from app.domains.inter_domain.system_unit.system_unit_query_provider import system_unit_query_provider
from app.domains.inter_domain.device_management.device_query_provider import device_management_query_provider

# --- [3] Command Providers: 실제 액션(상태 변경/복제) 위임 ---
from app.domains.inter_domain.device_management.device_command_provider import device_management_command_provider
from app.domains.inter_domain.hardware_blueprint.hardware_blueprint_command_provider import hardware_blueprint_command_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

logger = logging.getLogger(__name__)

class SystemUnitBindingPolicy:
    """
    [The Orchestrator]
    시스템 유닛과 기기 블록을 논리적/물리적으로 결합하는 과정을 조율합니다.
    본 클래스는 직접적인 비즈니스 로직(if/else 판단)을 가지지 않고 각 도메인을 지휘합니다.
    """

    def bind_device_to_unit(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        unit_id: int, 
        device_id: int, 
        role: str = "MASTER"
    ) -> Dict[str, Any]:
        """
        [Flow]
        1. 조회: 유닛과 기기 데이터를 가져옵니다.
        2. 검증: 결합이 가능한 상태(소유권, 중복 연결 여부 등)인지 검증기에 위임합니다.
        3. 실행: 기기를 유닛에 귀속시키고, 설계도(Blueprint)의 핀맵을 복제합니다.
        4. 확정: 모든 과정이 성공하면 DB에 커밋합니다.
        """
        try:
            # 1. 데이터 확보 (Query Services)
            unit = system_unit_query_provider.get_by_id(db, unit_id=unit_id)
            device = device_management_query_provider.get_by_id(db, device_id=device_id)

            # 2. 판단 위임 (Validator)
            # Policy는 정보를 넘겨주고 "괜찮은지"만 확인받습니다.
            validator = system_unit_binding_validator_provider.get_validator()
            validator.validate_binding_eligibility(
                user_id=user_id,
                unit=unit,
                device=device
            )

            # 3. 실행 명령 (Command Services)
            # A. 기기를 시스템 유닛의 멤버로 등록
            device_management_command_provider.assign_to_unit(
                db, 
                device_id=device_id, 
                unit_id=unit_id, 
                role=role
            )

            # B. 핀맵 복제 (설계도의 추상적 핀 정보를 기기의 실제 핀으로 구현)
            # unit.blueprint_id는 validator에서 이미 존재 여부가 검증되었다고 가정합니다.
            cloned_pins = hardware_blueprint_command_provider.clone_blueprint_to_device(
                db, 
                blueprint_id=unit.blueprint_id, 
                device_id=device_id
            )

            # 4. 감사 로그 기록
            audit_command_provider.log_event(
                db=db,
                event_type="DEVICE_UNIT_BIND_SUCCESS",
                description=f"Device {device_id} successfully bound to Unit {unit_id}",
                details={
                    "user_id": user_id,
                    "unit_id": unit_id,
                    "device_id": device_id,
                    "blueprint_id": unit.blueprint_id,
                    "cloned_pins_count": len(cloned_pins) if cloned_pins else 0
                }
            )

            # 5. 트랜잭션 확정
            db.commit()
            logger.info(f"✅ [Binding Policy] Device {device_id} <-> Unit {unit_id} 결합 성공")

            return {
                "status": "success",
                "message": "Device bound and pins cloned successfully.",
                "unit_id": unit_id,
                "device_id": device_id
            }

        except Exception as e:
            # 하나라도 실패하면 전체 과정을 되돌립니다.
            db.rollback()
            logger.error(f"❌ [Binding Policy] 결합 실패: {str(e)}")
            raise e

# 싱글톤 인스턴스 생성
system_unit_binding_policy = SystemUnitBindingPolicy()