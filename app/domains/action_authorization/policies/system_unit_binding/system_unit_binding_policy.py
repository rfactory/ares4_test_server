import logging
from sqlalchemy.orm import Session
from typing import Any, Dict

# --- [1] Inter-Domain Providers (조회 및 실행 인터페이스) ---
# 1. 설계도(Blueprint) 도메인: 레시피 조회
from app.domains.inter_domain.hardware_blueprint.hardware_blueprint_query_provider import hardware_blueprint_query_provider

# 2. 기기 관리(Device) 도메인: 기기 상태 및 소유권 조회/수정
from app.domains.inter_domain.device_management.device_query_provider import device_management_query_provider
from app.domains.inter_domain.device_management.device_command_provider import device_management_command_provider

# 3. 기기 부품(Component) 도메인: 핀맵 실체화 (The Realizer)
from app.domains.inter_domain.device_component_management.device_component_command_provider import device_component_command_provider

# 4. 시스템 유닛 도메인 (기존에 없던 것을 서비스 직접 참조 혹은 통합 Provider로 가정)
from app.domains.inter_domain.system_unit.system_unit_query_provider import system_unit_query_provider

# 5. 공통 기능
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
from app.models.objects.user import User

logger = logging.getLogger(__name__)

class SystemUnitBindingPolicy:
    """
    [The Orchestrator]
    시스템 유닛과 기기를 결합하고, 설계도 레시피를 기기에 심어주는 전체 과정을 지휘합니다.
    """

    def bind_device_to_unit(
        self, 
        db: Session, 
        *, 
        actor_user: User, 
        unit_id: int, 
        device_id: int, 
        role: str = "MASTER"
    ) -> Dict[str, Any]:
        """
        [Scenario C 연동] 기기를 유닛에 연결하고 초기 핀맵을 복제합니다.
        """
        try:
            # STEP 1: 데이터 수집
            unit = system_unit_query_provider.get_system_unit(db, id=unit_id)
            device = device_management_query_provider.get_by_id(db, id=device_id)

            # STEP 2: 검증 (Validator 호출 - 프로바이더가 없다면 직접 인스턴스화)
            # 여기서는 별도의 Validator 클래스를 호출하여 판단을 위임합니다.
            from app.domains.action_authorization.validators.system_unit_binding.validator import system_unit_binding_validator
            system_unit_binding_validator.validate_binding_eligibility(
                db=db, actor_user=actor_user, unit=unit, device=device
            )

            # STEP 3: 레시피(회로도) 확보
            # 유닛이 어떤 설계도(Blueprint)를 사용하는지 확인하여 핀 정보를 가져옵니다.
            recipe = hardware_blueprint_query_provider.get_blueprint_recipe(
                db, blueprint_id=unit.product_line.blueprint_id
            )

            # STEP 4: 실행 명령 (Command)
            
            # A. 기기의 소속 변경 (Device -> System Unit)
            device_management_command_provider.assign_to_unit(
                db, device_id=device_id, unit_id=unit_id, role=role
            )

            # B. 핀맵 실체화 (Cloning with Faulty Pin Awareness)
            # 이 명령은 내부적으로 기기의 고장난 핀(FAULTY)을 보존하고 새 배선을 깝니다.
            device_component_command_provider.reinitialize_components_by_recipe(
                db, 
                device_id=device_id, 
                recipe=recipe, 
                actor_user=actor_user
            )

            # STEP 5: 감사 로그 및 확정
            audit_command_provider.log_event(
                db=db,
                actor_user=actor_user,
                event_type="DEVICE_UNIT_BIND_SUCCESS",
                description=f"Device {device_id} bound to Unit {unit_id} as {role}",
                details={"unit_id": unit_id, "recipe_count": len(recipe)}
            )
            
            db.commit()
            return {"status": "success", "device_id": device_id, "unit_id": unit_id}

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Binding Failed: {str(e)}")
            raise e

system_unit_binding_policy = SystemUnitBindingPolicy()