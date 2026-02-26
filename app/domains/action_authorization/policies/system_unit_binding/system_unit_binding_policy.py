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
from app.models.objects.system_unit import SystemUnit as DBSystemUnit
from app.models.relationships.device_component_pin_mapping import PinStatusEnum

# --- [3] Schemas & Validators (타입 힌팅 및 검증) ---
from app.domains.action_authorization.validators.system_unit_binding.validator import system_unit_binding_validator
from app.domains.services.device_management.schemas.device_query import DeviceQuery
from app.domains.services.device_management.schemas.device_command import DeviceUpdate
from app.domains.services.hardware_blueprint.schemas.hardware_blueprint_query import BlueprintPinMappingRead

logger = logging.getLogger(__name__)

class SystemUnitBindingPolicy:
    """
    [The Orchestrator] 
    시나리오 C: 결합 및 지능형 우회 배선을 총괄하며, 모든 변경사항을 감사 로그로 남깁니다.
    """
    
    def promote_device_to_master(self, db: Session, *, actor_user: User, unit_id: int, device_id: int) -> Dict[str, Any]:
        """
        [Scenario B] 마스터(반장) 승격 정책.
        DB 역할을 교체하고, MQTT를 통해 기기들에게 Docker 도면 전환 명령을 쏩니다.
        """
        try:
            # 1. 데이터 확보 (사용자님의 CRUD 호출 방식 준수)
            unit_obj: Optional[DBSystemUnit] = system_unit_query_provider.get_service().system_unit_query_crud.get(db, id=unit_id)
            if not unit_obj: raise NotFoundError("SystemUnit", f"ID {unit_id}")

            target_device: Optional[DBDevice] = db.query(DBDevice).filter(DBDevice.id == device_id).first()
            if not target_device or target_device.system_unit_id != unit_id:
                raise AppLogicError(f"기기 {device_id}가 유닛 {unit_id}에 속해있지 않아 반장이 될 수 없습니다.")

            # 2. [Atomic Change] DB 상의 임명장 교체
            # 기존 마스터 색출 및 강등 (Leader -> Follower)
            old_master = db.query(DBDevice).filter(
                DBDevice.system_unit_id == unit_id, 
                DBDevice.cluster_role == ClusterRoleEnum.LEADER
            ).first()
            
            if old_master:
                old_master.cluster_role = ClusterRoleEnum.FOLLOWER
                logger.info(f"📉 기존 마스터 {old_master.id} 강등.")

            # 새 마스터 임명 (Follower -> Leader)
            target_device.cluster_role = ClusterRoleEnum.LEADER
            unit_obj.master_device_id = target_device.id
            db.flush()

            # 3. [Edge Sync] 소프트웨어 도면 교체 명령 (MQTT)
            # 기기들은 이 메시지를 받고 자신의 ID와 비교하여 마스터 전용 Docker 템플릿을 활성화합니다.
            mqtt_topic = f"ares4/units/{unit_id}/cluster_control"
            command_payload = {
                "action": "SYNC_CLUSTER_ROLES",
                "master_device_id": target_device.id, 
                "instruction": "RELOAD_DOCKER_ROLES",
                "timestamp": str(db.query(func.now()).scalar())
            }
            
            publish_command(db, topic=mqtt_topic, command=command_payload, actor_user=actor_user)
            logger.info(f"📡 유닛 {unit_id}에 실시간 반장 교체 명령 발송 완료.")

            # 4. 감사 로그 기록
            audit_command_provider.log(
                db=db, event_type="SYSTEM_UNIT_STATUS_CHANGED",
                description=f"Master Rotated: {old_master.id if old_master else 'None'} -> {device_id}",
                actor_user=actor_user, target_device=target_device,
                details={"unit_id": unit_id, "new_master": device_id}
            )

            db.commit()
            return {"status": "success", "unit_id": unit_id, "master_id": device_id}

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Master Promotion Failure: {str(e)}")
            raise e
    
    def bind_device_to_unit(self, db: Session, *, actor_user: User, unit_id: int, device_id: int, role: str) -> Dict[str, Any]:
        """[Step 1-4] 신규 기기 결합 및 초기 우회 배선"""
        try:
            internal_role = ClusterRoleEnum.LEADER if role == "MASTER" else role

            # 1. 모델 원본 확보 (서비스 내부 CRUD 속성 활용 - AttributeError 해결)
            unit_obj: Optional[DBSystemUnit] = system_unit_query_provider.get_service().system_unit_query_crud.get(db, id=unit_id)
            if not unit_obj: raise NotFoundError("SystemUnit", f"ID {unit_id}")
            
            device_obj: Optional[DBDevice] = device_management_query_provider.get_service().device_query_crud.get(db, id=device_id)
            if not device_obj: raise NotFoundError("Device", f"ID {device_id}")

            # 2. 유닛 가용량 판단 (구독 정보 참조)
            sub = unit_obj.subscription or unit_obj.user_subscription
            max_capacity = sub.max_devices if sub and sub.max_devices else 10

            # 3. 소유권 및 결합 적합성 검증
            is_unit_owner = system_unit_assignment_query_provider.is_user_assigned_to_unit(db, user_id=actor_user.id, unit_id=unit_id)
            system_unit_binding_validator.validate_binding_eligibility(
                actor_user_id=actor_user.id, device_obj=device_obj, unit_obj=unit_obj,
                is_unit_owner=is_unit_owner, 
                current_device_count=device_management_query_provider.get_count_by_unit(db, unit_id=unit_id),
                max_capacity=max_capacity, requested_role=role,
                has_existing_master=device_management_query_provider.has_master_device(db, unit_id=unit_id)
            )

            # 4. [Rerouting Engine] 지능형 우회
            # BlueprintPinMapping 모델 확인 결과 role 구분 필드가 없으므로 전체 레시피를 할당합니다.
            all_recipes: List[BlueprintPinMappingRead] = hardware_blueprint_query_provider.get_blueprint_recipe(db, blueprint_id=unit_obj.product_line_id)
            pin_pool = hardware_blueprint_query_provider.get_valid_pin_pool(db, blueprint_id=unit_obj.product_line_id)
            
            # 고장 핀을 감지하여 초기 레시피를 수정 (db를 넘겨 로그 기록 가능케 함)
            final_recipe = self._calculate_rerouted_recipe(db, device_obj, all_recipes, pin_pool)

            # 5. 실행 명령
            device_management_command_provider.assign_to_unit(db, device_id=device_id, unit_id=unit_id, role=internal_role)
            device_component_command_provider.reinitialize_components_by_recipe(
                db, device_id=device_id, recipe=final_recipe, actor_user=actor_user
            )

            # 6. 감사 로그 기록
            audit_command_provider.log(
                db=db, event_type="SYSTEM_UNIT_BIND_SUCCESS",
                description=f"Device {device_id} bound to Unit {unit_id} as {internal_role}",
                actor_user=actor_user, target_device=device_obj,
                details={"unit_id": unit_id, "role": internal_role}
            )

            db.commit()
            return {"status": "success", "device_id": device_id}

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Policy Failure: {str(e)}")
            raise e

    def claim_unit_and_inherit_devices(self, db: Session, *, actor_user: User, unit_id: int) -> Dict[str, Any]:
        """[Step 5] 유닛 점유 및 소속 기기 소유권 일괄 승계"""
        try:
            # 1. 유닛 소유권 할당 (확인된 메서드명 assign_owner 사용)
            system_unit_assignment_command_provider.assign_owner(db, unit_id=unit_id, user_id=actor_user.id)

            # 2. 소속 기기 일괄 승계
            attached_devices = device_management_query_provider.get_devices(db, query_params=DeviceQuery(system_unit_id=unit_id))
            
            for d_read in attached_devices:
                # 기기 소유자 업데이트
                update_in = DeviceUpdate(owner_user_id=actor_user.id)
                device_management_command_provider.update_device(db, device_id=d_read.id, obj_in=update_in, actor_user=actor_user)
                
                # [핵심] 승계 시점 고장 핀 전수 조사 및 DB 업데이트 우회 실행
                db_device = device_management_query_provider.get_service().device_query_crud.get(db, id=d_read.id)
                if db_device:
                    self._reroute_existing_faulty_pins(db, device=db_device)

            # 3. 감사 로그 기록
            audit_command_provider.log(
                db=db, event_type="SYSTEM_UNIT_CLAIM_SUCCESS",
                description=f"User {actor_user.id} claimed Unit {unit_id} and inherited {len(attached_devices)} devices",
                actor_user=actor_user, details={"unit_id": unit_id}
            )

            db.commit()
            return {"status": "success", "unit_id": unit_id, "inherited_count": len(attached_devices)}
        except Exception as e:
            db.rollback()
            raise e

    def _calculate_rerouted_recipe(self, db: Session, device: DBDevice, recipe: List[BlueprintPinMappingRead], pin_pool: List[int]) -> List[BlueprintPinMappingRead]:
        """[Initial Rerouter] 초기 결합 시 레시피 객체를 수정하여 전달합니다."""
        faulty_pin_nos = {m.pin_number for m in device.pin_mappings if m.status == PinStatusEnum.FAULTY}
        if not faulty_pin_nos: return recipe

        used_in_recipe = {r.pin_number for r in recipe if r.pin_number is not None}
        available_pins = [p for p in pin_pool if p not in faulty_pin_nos and p not in used_in_recipe]

        for item in recipe:
            if item.pin_number in faulty_pin_nos:
                if not available_pins:
                    logger.error(f"❌ Device {device.id}: 대체 핀 부족")
                    continue
                new_pin = available_pins.pop(0)
                audit_command_provider.log_event(
                    db=db, event_type="DEVICE_REROUTED",
                    description=f"Initial Pin {item.pin_name} rerouted to {new_pin} due to hardware fault",
                    details={"device_id": device.id, "old_pin": item.pin_number, "new_pin": new_pin}
                )
                item.pin_number = new_pin
        return recipe

    def _reroute_existing_faulty_pins(self, db: Session, *, device: DBDevice) -> None:
        """[Migration Rerouter] 이미 DB에 박힌 핀 매핑 중 고장 난 것들을 찾아 대체합니다."""
        faulty_mappings = [m for m in device.pin_mappings if m.status == PinStatusEnum.FAULTY]
        if not faulty_mappings: return

        pin_pool = hardware_blueprint_query_provider.get_valid_pin_pool(db, blueprint_id=device.hardware_blueprint_id)
        used_pins = {m.pin_number for m in device.pin_mappings if m.pin_number is not None}
        available_candidates = [p for p in pin_pool if p not in used_pins]

        for mapping in faulty_mappings:
            if not available_candidates:
                logger.error(f"❌ Device {device.id}: 승계 중 우회 가능한 핀 고갈")
                break
            
            old_pin = mapping.pin_number
            new_pin = available_candidates.pop(0)
            mapping.pin_number = new_pin # 실질적인 DB 컬럼 업데이트
            
            audit_command_provider.log_event(
                db=db, event_type="DEVICE_REROUTED",
                description=f"Existing Pin {mapping.pin_name} rerouted from {old_pin} to {new_pin} during ownership claim",
                details={"device_id": device.id, "old_pin": old_pin, "new_pin": new_pin}
            )
        db.flush()

system_unit_binding_policy = SystemUnitBindingPolicy()