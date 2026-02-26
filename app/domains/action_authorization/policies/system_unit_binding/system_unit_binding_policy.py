import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Any, Dict, List, Optional
from app.core.exceptions import NotFoundError, AppLogicError

# --- [1] Inter-Domain Providers (공공 인터페이스 호출) ---
# 1. 설계도 도메인
from app.domains.inter_domain.hardware_blueprint.hardware_blueprint_query_provider import hardware_blueprint_query_provider

# 2. 기기 관리 도메인
from app.domains.inter_domain.device_management.device_query_provider import device_management_query_provider
from app.domains.inter_domain.device_management.device_command_provider import device_management_command_provider

# 3. 부품/배선 도메인
from app.domains.inter_domain.device_component_management.device_component_command_provider import device_component_command_provider

# 4. 시스템 유닛 도메인
from app.domains.inter_domain.system_unit.system_unit_query_provider import system_unit_query_provider
from app.domains.inter_domain.system_unit.system_unit_command_provider import system_unit_command_provider

# 5. 할당/권한 도메인 (명칭: assign_owner 및 create_assignment 확인)
from app.domains.inter_domain.system_unit_assignment.system_unit_assignment_query_provider import system_unit_assignment_query_provider
from app.domains.inter_domain.system_unit_assignment.system_unit_assignment_command_provider import system_unit_assignment_command_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
from app.domains.inter_domain.command_dispatch.command_dispatch_provider import publish_command

# --- [2] Models & Enums (DB 원본 규격 - 흰색 에러 해결) ---
from app.models.objects.user import User
from app.models.objects.device import Device as DBDevice, ClusterRoleEnum
from app.models.objects.system_unit import SystemUnit as DBSystemUnit, UnitStatus
from app.models.relationships.device_component_pin_mapping import PinStatusEnum

# --- [3] Schemas & Validators (타입 힌팅 및 검증) ---
from app.domains.inter_domain.validators.system_unit_binding.system_unit_binding_validator_provider import system_unit_binding_validator_provider
from app.domains.inter_domain.device_management.schemas.device_query import DeviceQuery
from app.domains.inter_domain.device_management.schemas.device_command import DeviceUpdate
from app.domains.inter_domain.hardware_blueprint.schemas.models import HardwareBlueprintRead

logger = logging.getLogger(__name__)

class SystemUnitBindingPolicy:
    """
    [The Orchestrator] 
    Ares4 기기 관리의 최종 권위자입니다. 
    공학적 정원(ProductLine)과 비즈니스 권한(Subscription)을 엄격히 분리하여 집행합니다.
    """
    
    def promote_device_to_master(self, db: Session, *, actor_user: User, unit_id: int, device_id: int) -> Dict[str, Any]:
        """
        [Scenario B] 마스터(반장) 승격 정책.
        DB 역할을 교체하고, MQTT를 통해 기기들에게 Docker 도면 전환 명령을 쏩니다.
        """
        try:
            # 1. 정보 확보
            unit_obj = system_unit_query_provider.get_service().system_unit_query_crud.get(db, id=unit_id)
            if not unit_obj: raise NotFoundError("SystemUnit", f"ID {unit_id}")
            target_device = device_management_query_provider.get_service().device_query_crud.get(db, id=device_id)

            # 2. 판단 위임 (이제 validate_promotion_eligibility에 색상이 들어옵니다)
            system_unit_binding_validator_provider.validate_promotion_eligibility(
                unit_id=unit_id, target_device=target_device, device_id=device_id
            )

            # 3. 조작 위임
            device_management_command_provider.rotate_master(db, unit_id=unit_id, new_master_id=device_id)

            # 4. 동기화 및 기록
            mqtt_topic = f"ares4/units/{unit_id}/cluster_control"
            publish_command(db, topic=mqtt_topic, command={"action": "SYNC_CLUSTER_ROLES", "master_device_id": device_id}, actor_user=actor_user)
            audit_command_provider.log(db=db, event_type="SYSTEM_UNIT_STATUS_CHANGED", actor_user=actor_user, details={"unit_id": unit_id})

            db.commit()
            return {"status": "success", "master_id": device_id}
        except Exception as e:
            db.rollback()
            raise e
    
    def bind_device_to_unit(self, db: Session, *, actor_user: User, unit_id: int, device_id: int, role: str) -> Dict[str, Any]:
        """
        [Step 5.2.3 Physical Binding] 기기 결합 오케스트레이션.
        공학적 규격 확인과 물리적 배선 실체화를 전문가들에게 하달합니다.
        """
        try:
            # 1. 정보 확보 (Query Provider 활용)
            unit_obj = system_unit_query_provider.get_service().system_unit_query_crud.get(db, id=unit_id)
            device_obj = device_management_query_provider.get_service().device_query_crud.get(db, id=device_id)
            
            is_unit_owner = system_unit_assignment_query_provider.is_user_assigned_to_unit(db, user_id=actor_user.id, unit_id=unit_id)
            current_count = device_management_query_provider.get_count_by_unit(db, unit_id=unit_id)
            has_master = device_management_query_provider.has_master_device(db, unit_id=unit_id)

            # 2. 판단 위임 (Judge: Validator Provider)
            # [수정] 직접 if문으로 정원을 체크하던 로직은 이제 validator가 수행합니다.
            system_unit_binding_validator_provider.validate_binding_eligibility(
                actor_user_id=actor_user.id,
                device_obj=device_obj,
                unit_obj=unit_obj,
                is_unit_owner=is_unit_owner,
                current_device_count=current_count,
                requested_role=role,
                has_existing_master=has_master
            )

            # 3. 조작 명령 (Realizers: Command Providers)
            
            # A. 기기-유닛 귀속 (Device Domain)
            device_management_command_provider.assign_to_unit(db, device_id=device_id, unit_id=unit_id, role=role)

            # B. 지능형 우회 배선 실체화 (Component Domain - 엔진 가동)
            # [수정] 직접 레시피를 계산하던 로직을 Provider의 '스마트 엔진' 호출로 대체합니다.
            recipe = hardware_blueprint_query_provider.get_blueprint_recipe(db, blueprint_id=unit_obj.product_line_id)
            pin_pool = hardware_blueprint_query_provider.get_valid_pin_pool(db, blueprint_id=unit_obj.product_line_id)
            
            device_component_command_provider.reinitialize_with_smart_rerouting(
                db, 
                device_obj=device_obj, 
                raw_recipe=recipe, 
                pin_pool=pin_pool, 
                actor_user=actor_user
            )

            # C. 유닛 가동 상태 동기화 (SystemUnit Domain)
            # [수정] 직접 상태를 체크하던 로직을 Provider의 '상태 동기화' 명령으로 대체합니다.
            system_unit_command_provider.sync_activation_status(db, unit_id=unit_id, actor_user=actor_user)

            # 4. 기록 및 확정
            audit_command_provider.log(
                db=db, 
                event_type="SYSTEM_UNIT_BIND_SUCCESS", 
                description=f"Device {device_id} physically bound to Unit {unit_id}", 
                actor_user=actor_user, 
                target_device=device_obj, 
                details={"unit_id": unit_id}
            )

            db.commit()
            return {"status": "success", "device_id": device_id}

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Physical Binding Failure: {str(e)}")
            raise e

    def claim_unit_and_inherit_devices(self, db: Session, *, actor_user: User, unit_id: int) -> Dict[str, Any]:
        """
        [Step 5.2.1 Ownership Claim] 유닛 점유 및 소속 기기 소유권 일괄 승계.
        비즈니스 권한 할당과 물리적 기기 승계를 순서대로 조율합니다.
        """
        try:
            # 1. 유닛 소유권 할당 (Assignment Domain)
            # 비즈니스 구독 한도 체크는 이 안에서 수행됩니다.
            system_unit_assignment_command_provider.assign_owner(db, unit_id=unit_id, user_id=actor_user.id)

            # 2. 소속 기기 일괄 승계 조율
            # A. 현재 유닛에 꽂혀있는 기기 목록 확보
            attached_devices = device_management_query_provider.get_devices(
                db, query_params=DeviceQuery(system_unit_id=unit_id)
            )
            
            for d_read in attached_devices:
                # B. 기기 소유권 변경 및 모델 객체 확보 (Device Domain)
                # 업데이트 후 반환되는 DB 모델 객체를 사용하여 다음 단계로 넘깁니다.
                updated_device = device_management_command_provider.update_device(
                    db, device_id=d_read.id, 
                    obj_in=DeviceUpdate(owner_user_id=actor_user.id), 
                    actor_user=actor_user
                )

                # C. 승계 시점 고장 핀 복구 엔진 가동 (Component Domain)
                # [수정] 직접 깎지 않고 정비된 'reroute_faulty_pins' 전문가를 호출합니다.
                if updated_device and updated_device.hardware_blueprint_id:
                    pin_pool = hardware_blueprint_query_provider.get_valid_pin_pool(
                        db, blueprint_id=updated_device.hardware_blueprint_id
                    )
                    device_component_command_provider.reroute_faulty_pins(
                        db, device_obj=updated_device, pin_pool=pin_pool, actor_user=actor_user
                    )
            
            # 3. 감사 로그 기록
            audit_command_provider.log(
                db=db, 
                event_type="SYSTEM_UNIT_CLAIM_SUCCESS", 
                description=f"User {actor_user.id} claimed Unit {unit_id} and inherited {len(attached_devices)} devices", 
                actor_user=actor_user, 
                details={"unit_id": unit_id, "inherited_count": len(attached_devices)}
            )
            
            db.commit()
            return {"status": "success", "unit_id": unit_id, "inherited_count": len(attached_devices)}
        
        except Exception as e:
            db.rollback()
            raise e

system_unit_binding_policy = SystemUnitBindingPolicy()