import logging
from sqlalchemy.orm import Session
from typing import Any, Dict, List
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
from app.domains.inter_domain.system_unit_assignment.system_unit_assignment_command_provider import system_unit_assignment_command_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
from app.models.objects.user import User
from app.models.objects.device import Device as DBDevice
from app.models.relationships.device_component_pin_mapping import DeviceComponentPinMapping, PinStatusEnum

# 6. 검증 로직 (Validator) - 정책에서 직접 호출하여 판단을 위임
from app.domains.action_authorization.validators.system_unit_binding.validator import system_unit_binding_validator

from app.domains.services.device_management.schemas.device_query import DeviceQuery
from app.domains.services.device_management.schemas.device_command import DeviceUpdate
from app.models.relationships.system_unit_assignment import AssignmentRoleEnum

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

            # 2. 실제 상태 확인
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

            # 4. 레시피 확보 및 필터링 (신규 추가 로직)
            full_recipe = hardware_blueprint_query_provider.get_blueprint_recipe(db, blueprint_id=blueprint.id)
            # [핵심] 설계도 전체 핀맵 중, 현재 기기가 맡은 역할(role)에 해당하는 배선 정보만 추출합니다.
            role_recipe = [r for r in full_recipe if r.role == role]
            
            if not role_recipe:
                logger.warning(f"⚠️ 설계도 {blueprint.id}에 {role} 역할에 정의된 배선 정보가 없습니다.")

            # 5. 실행 명령 (Atomic Transaction)
            device_management_command_provider.assign_to_unit(db, device_id=device_id, unit_id=unit_id, role=role)
            
            # B. 핀맵 실체화 실행 (필터링된 role_recipe만 기기에 복제)
            device_component_command_provider.reinitialize_components_by_recipe(
                db, device_id=device_id, recipe=role_recipe, actor_user=actor_user
            )
            
            # --- [핵심 추가: 완결성 체크 및 유닛 상태 제어] ---
            # 이번에 결합한 기기를 포함한 총 대수 계산
            new_total_count = current_count + 1
            
            if new_total_count == max_capacity:
                # 설계도 수량을 모두 채웠다면 유닛을 '가동 가능(ACTIVE)' 상태로 변경
                system_unit_command_provider.update_unit_status(db, unit_id=unit_id, status="ACTIVE", actor_user=actor_user)
                logger.info(f"✨ 유닛 {unit_id}의 모든 기기가 채워졌습니다. 가동을 시작합니다.")
            else:
                # 아직 기기가 부족하다면 '준비 중' 상태 유지 (혹은 강제 비활성화)
                system_unit_command_provider.update_unit_status(db, unit_id=unit_id, status="PROVISIONING", actor_user=actor_user)
                logger.warning(f"⚠️ 유닛 {unit_id}에 기기가 더 필요합니다. ({new_total_count}/{max_capacity})")

            # 6. 결과 기록 및 확정
            audit_command_provider.log_event(
                db=db,
                actor_user=actor_user,
                event_type="DEVICE_UNIT_BIND_SUCCESS",
                description=f"Device {device_id} bound to Unit {unit_id} as {role}",
                details={"unit_id": unit_id, "pin_count": len(role_recipe), "role": role}
            )
            
            db.commit()
            return {"status": "success", "device_id": device_id, "unit_id": unit_id, "role": role, "is_complete": new_total_count == max_capacity}

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Policy Failure: {str(e)}")
            raise e

    def claim_unit_and_inherit_devices(self, db: Session, *, actor_user: User, unit_id: int) -> Dict[str, Any]:
        """
        [Scenario C - Step 5: Atomic Fusion] 
        새 주인이 QR을 찍었을 때 유닛 소유권 등록 및 소속 기기 일괄 승계를 처리합니다.
        """
        try:
            # A. 유닛 소유권 등록 (시스템 유닛 어사인먼트 생성)
            system_unit_assignment_command_provider.create_assignment(
                db, system_unit_id=unit_id, user_id=actor_user.id, role="OWNER"
            )

            # B. 소속 기기 일괄 승계 (실제 존재하는 get_devices 필터 사용)
            query_params = DeviceQuery(system_unit_id=unit_id)
            attached_devices_read = device_management_query_provider.get_devices(db, query_params=query_params)
            
            for d_read in attached_devices_read:
                # 1. 기기 소유권 업데이트 (실존하는 update_device와 DeviceUpdate 스키마 사용)
                update_data = DeviceUpdate(owner_user_id=actor_user.id)
                device_management_command_provider.update_device(
                    db, device_id=d_read.id, obj_in=update_data, actor_user=actor_user
                )
                
                # 2. 고장 핀 발견 시 자동 우회 (우회를 위해 DB 모델 객체 획득)
                db_device = db.query(DBDevice).filter(DBDevice.id == d_read.id).first()
                if db_device:
                    self.check_and_reroute_faulty_pins(db, device=db_device)

            # C. 유닛 상태 활성화
            system_unit_command_provider.update_unit_status(db, unit_id=unit_id, status="ACTIVE", actor_user=actor_user)

            db.commit()
            return {"status": "success", "unit_id": unit_id, "inherited_count": len(attached_devices_read)}

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Claim Policy Failure: {str(e)}")
            raise e

    def check_and_reroute_faulty_pins(self, db: Session, *, device: DBDevice):
        """
        [The Rerouter] 기기의 고장 핀을 감지하여 다른 핀으로 우회 배선합니다.
        """
        # DB 모델을 직접 받으므로 device.pin_mappings 접근 가능 (흰색 에러 해결)
        current_mappings: List[DeviceComponentPinMapping] = device.pin_mappings
        faulty_mappings = [m for m in current_mappings if m.status == "FAULTY"]

        if not faulty_mappings:
            return

        logger.info(f"⚡ 기기 {device.id}에서 고장 핀 발견. 우회 배선 엔진 가동.")

        # 설계도 정보 획득 (가용 핀 목록을 위해 레시피 조회)
        recipe = hardware_blueprint_query_provider.get_blueprint_recipe(db, blueprint_id=device.hardware_blueprint_id)
        
        # [핵심] 해당 설계도에서 허용하는 전체 물리 핀 목록 (가정: recipe에 모든 정보가 있음)
        valid_pins = {r.pin_number for r in recipe}
        used_pins = {m.pin_number for m in current_mappings}
        
        # 고장 나지 않았고 사용 중이지 않은 핀들만 후보군으로 추출
        available_candidates = [p for p in valid_pins if p not in used_pins]

        for mapping in faulty_mappings:
            if not available_candidates:
                logger.error(f"❌ 기기 {device.id}에 여유 핀이 없어 우회가 불가능합니다.")
                break
            
            new_pin = available_candidates.pop(0)
            old_pin = mapping.pin_number
            
            # 실질적인 우회 배선 (Rerouting)
            mapping.pin_number = new_pin
            logger.info(f"✅ 우회 성공: {old_pin}번(고장) -> {new_pin}번(대체)")

        db.flush()
system_unit_binding_policy = SystemUnitBindingPolicy()