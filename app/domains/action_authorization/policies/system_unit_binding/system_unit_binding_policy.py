import logging
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional
from app.core.exceptions import NotFoundError

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
from app.domains.inter_domain.system_unit.system_unit_command_provider import system_unit_command_provider

# 5. 공통 기능
from app.domains.inter_domain.system_unit_assignment.system_unit_assignment_query_provider import system_unit_assignment_query_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
from app.models.objects.user import User

# 6. 검증 로직 (Validator) - 정책에서 직접 호출하여 판단을 위임
from app.domains.action_authorization.validators.system_unit_binding.validator import system_unit_binding_validator

logger = logging.getLogger(__name__)

class SystemUnitBindingPolicy:
    """
    [The Orchestrator]
    시스템 유닛과 기기를 결합하고, 설계도 레시피를 기기에 심어주는 전체 과정을 지휘합니다.
    """

    def bind_device_to_unit(self, db: Session, *, actor_user: User, unit_id: int, device_id: int, role: str) -> Dict[str, Any]:
        """
        [Scenario C 연동] 기기를 유닛에 연결하고 초기 핀맵을 복제합니다.
        """
        try:
            # 1. 데이터 수집
            unit = system_unit_query_provider.get_by_id(db, unit_id=unit_id)
            if not unit: raise NotFoundError("SystemUnit", f"ID {unit_id}를 찾을 수 없습니다.")
            
            device = device_management_query_provider.get_device_by_id(db, id=device_id)
            if not device: raise NotFoundError("Device", f"ID {device_id}를 찾을 수 없습니다.")
            
            blueprint = hardware_blueprint_query_provider.get_blueprint_by_id(db, id=unit.product_line_id)
            if not blueprint: raise NotFoundError("HardwareBlueprint", f"ID {unit.product_line_id}를 찾을 수 없습니다.")

            ## 2. 실제 상태 확인
            is_unit_owner = system_unit_assignment_query_provider.is_user_assigned_to_unit(db, user_id=actor_user.id, unit_id=unit_id)
            current_count = device_management_query_provider.get_count_by_unit(db, unit_id=unit_id)
            max_capacity = getattr(blueprint, 'max_devices')
            has_master = device_management_query_provider.has_master_device(db, unit_id=unit_id)

            # 3. 엄격한 검증
            system_unit_binding_validator.validate_binding_eligibility(
                actor_user_id=actor_user.id, device_obj=device, unit_obj=unit,
                is_unit_owner=is_unit_owner, current_device_count=current_count,
                max_capacity=max_capacity, requested_role=role, has_existing_master=has_master
            )

            # 4. 레시피 확보
            recipe = hardware_blueprint_query_provider.get_blueprint_recipe(db, blueprint_id=blueprint.id)

            # 5. 실행 명령 (Atomic Transaction)
            device_management_command_provider.assign_to_unit(db, device_id=device_id, unit_id=unit_id, role=role)
            
            # B. 핀맵 실체화 실행
            device_component_command_provider.reinitialize_components_by_recipe(db, device_id=device_id, recipe=recipe, actor_user=actor_user)
            
            # --- [핵심 추가: 완결성 체크 및 유닛 상태 제어] ---
            # 이번에 결합한 기기를 포함한 총 대수 계산
            new_total_count = current_count + 1
            
            if new_total_count == max_capacity:
                # 설계도 수량을 모두 채웠다면 유닛을 '가동 가능(ACTIVE)' 상태로 변경
                system_unit_command_provider.update_unit_status(db, unit_id=unit_id, status="ACTIVE")
                logger.info(f"✨ 유닛 {unit_id}의 모든 기기가 채워졌습니다. 가동을 시작합니다.")
            else:
                # 아직 기기가 부족하다면 '준비 중' 상태 유지 (혹은 강제 비활성화)
                system_unit_command_provider.update_unit_status(db, unit_id=unit_id, status="PROVISIONING")
                logger.warning(f"⚠️ 유닛 {unit_id}에 기기가 더 필요합니다. ({new_total_count}/{max_capacity})")

            # 6. 결과 기록 및 확정
            audit_command_provider.log_event(
                db=db,
                actor_user=actor_user,
                event_type="DEVICE_UNIT_BIND_SUCCESS",
                description=f"Device {device_id} bound to Unit {unit_id} as {role}",
                details={"unit_id": unit_id, "pin_count": len(recipe), "role": role}
            )
            
            db.commit()
            return {"status": "success", "device_id": device_id, "unit_id": unit_id, "is_complete": new_total_count == max_capacity}

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Policy Failure: {str(e)}")
            raise e

system_unit_binding_policy = SystemUnitBindingPolicy()