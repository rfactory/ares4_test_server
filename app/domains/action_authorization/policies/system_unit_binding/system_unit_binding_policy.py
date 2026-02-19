import logging
from sqlalchemy.orm import Session
from typing import Any, Dict

# --- [1] Inter-Domain Providers (조회 및 실행 인터페이스) ---
# 도메인 간 통신은 모두 inter_domain 디렉토리를 거칩니다.

# 조회(Query) 관련
from app.domains.inter_domain.system_unit.system_unit_query_provider import system_unit_query_provider
from app.domains.inter_domain.device_management.device_query_provider import device_management_query_provider

# 검증(Validator) 관련
from app.domains.inter_domain.validators.system_unit_binding.provider import system_unit_binding_validator_provider

# 실행(Command) 관련 (로직은 app/domains/services에 구현됨)
from app.domains.inter_domain.device_management.device_command_provider import device_management_command_provider
from app.domains.inter_domain.hardware_blueprint.hardware_blueprint_command_provider import hardware_blueprint_command_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

logger = logging.getLogger(__name__)

class SystemUnitBindingPolicy:
    """
    [The Orchestrator]
    경로: app/domains/action_authorization/policies/system_unit_binding/system_unit_binding_policy.py
    
    역할: 
    - 시스템 유닛과 기기 블록을 결합하는 '지휘관'입니다.
    - 비즈니스 판단은 Validator(action_authorization/validators)에 맡깁니다.
    - 실제 DB 작업은 Services(domains/services)에 명령합니다.
    - 도메인 간의 연결은 Inter-domain Providers를 사용합니다.
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
        사용자의 기기를 시스템 유닛에 바인딩하고 핀맵을 복제하는 전체 프로세스를 조율합니다.
        """
        try:
            # STEP 1: 데이터 수집 (Query Providers 호출)
            # inter_domain을 통해 각 도메인의 정보를 가져옵니다.
            unit = system_unit_query_provider.get_by_id(db, unit_id=unit_id)
            device = device_management_query_provider.get_by_id(db, device_id=device_id)

            # STEP 2: 판단 위임 (Validator Provider 호출)
            # Policy는 "이 결합이 정당한가?"를 직접 if문으로 판단하지 않습니다.
            # 로직 위치: app/domains/action_authorization/validators/system_unit_binding/
            validator = system_unit_binding_validator_provider.get_validator()
            validator.validate_binding_eligibility(
                user_id=user_id,
                unit=unit,
                device=device
            )

            # STEP 3: 실행 명령 (Command Providers 호출)
            # 실제 작업 위치: app/domains/services/
            
            # A. 물리적 귀속 설정 (Device -> SystemUnit)
            device_management_command_provider.assign_to_unit(
                db, 
                device_id=device_id, 
                unit_id=unit_id, 
                role=role
            )

            # B. 피라미드 복제 (설계도 -> 실제 핀 매핑 생성)
            # 설계도(Blueprint)의 추상적인 핀 정보를 기기의 실제 데이터로 변환합니다.
            cloned_pins = hardware_blueprint_command_provider.clone_blueprint_to_device(
                db, 
                blueprint_id=unit.blueprint_id, 
                device_id=device_id
            )

            # STEP 4: 기록 및 감사
            audit_command_provider.log_event(
                db=db,
                event_type="DEVICE_UNIT_BIND_SUCCESS",
                description=f"User {user_id} bound Device {device_id} to Unit {unit_id}",
                details={
                    "unit_id": unit_id,
                    "device_id": device_id,
                    "blueprint_id": unit.blueprint_id,
                    "cloned_pins_count": len(cloned_pins) if cloned_pins else 0
                }
            )

            # STEP 5: 트랜잭션 최종 확정 (Commit)
            # 모든 서비스 액션이 성공했을 때만 한꺼번에 저장합니다.
            db.commit()
            logger.info(f"✅ [Policy] Binding Success: Unit {unit_id} <-> Device {device_id}")

            return {
                "status": "success",
                "message": "Device successfully bound to unit and pins initialized.",
                "unit_id": unit_id,
                "device_id": device_id
            }

        except Exception as e:
            # 하나라도 실패하면 전체 과정을 되돌려 데이터 무결성을 지킵니다.
            db.rollback()
            logger.error(f"❌ [Policy] Binding Failed: {str(e)}")
            raise e

# 싱글톤 인스턴스
system_unit_binding_policy = SystemUnitBindingPolicy()