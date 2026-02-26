import logging
from sqlalchemy.orm import Session
from typing import List

# --- Model Imports ---
from app.models.relationships.device_component_instance import DeviceComponentInstance
from app.models.relationships.device_component_pin_mapping import DeviceComponentPinMapping, PinStatusEnum
from app.models.objects.user import User
from app.models.objects.device import Device as DBDevice # 타입 힌팅용

# --- Schema Imports (Policy로부터 전달받을 데이터 타입) ---
from app.domains.services.hardware_blueprint.schemas.hardware_blueprint_query import BlueprintPinMappingRead
from ..schemas.device_component_instance_command import DeviceComponentInstanceCreate

# --- Provider Imports ---
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

logger = logging.getLogger(__name__)

class DeviceComponentInstanceCommandService:
    """
    [Pure Command Service]
    판단(조회/검증)을 배제하고, Policy가 전달한 설계도(레시피)를 
    실제 기기의 물리적 핀 매핑으로 구현(Write)하는 데 집중합니다.
    """

    def reinitialize_components_by_recipe(
        self, db: Session, *, device_id: int, recipe: List[BlueprintPinMappingRead], actor_user: User
    ) -> None:
        """[The Realizer] 기존 설정을 밀고(고장 제외) 새 배선을 실행합니다."""
        
        # 1. 기존 데이터 정리 (고장난 핀(FAULTY) 기록은 절대 지우지 않음)
        db.query(DeviceComponentPinMapping).filter(
            DeviceComponentPinMapping.device_id == device_id,
            DeviceComponentPinMapping.status != PinStatusEnum.FAULTY # [중요] FAULTY 제외
        ).delete()
        
        # 인스턴스는 배선이 새로 깔리므로 일단 모두 제거
        db.query(DeviceComponentInstance).filter(DeviceComponentInstance.device_id == device_id).delete()
        db.flush()

        # 2. 레시피(BlueprintPinMappingRead)를 바탕으로 실체화
        for item in recipe:
            # 부품 인스턴스 생성
            new_instance = DeviceComponentInstance(
                device_id=device_id,
                supported_component_id=item.supported_component_id,
                instance_name=item.pin_name,
                configuration={}
            )
            db.add(new_instance)
            db.flush()

            # B. 핀 매핑 생성 (실제 배선)
            new_mapping = DeviceComponentPinMapping(
                device_id=device_id,
                device_component_instance_id=new_instance.id,
                pin_name=item.pin_name,
                pin_number=item.pin_number,
                pin_mode=item.pin_mode,
                status=PinStatusEnum.ACTIVE
            )
            db.add(new_mapping)

        # 3. 감사 로그 기록
        audit_command_provider.log_event(
            db=db,
            actor_user=actor_user,
            event_type="DEVICE_COMPONENTS_REINITIALIZED",
            description=f"Device {device_id} components reinitialized based on blueprint recipe.",
            details={"device_id": device_id, "recipe_count": len(recipe)}
        )
        db.flush()

    def create_instance(self, db: Session, *, obj_in: DeviceComponentInstanceCreate, actor_user: User) -> DeviceComponentInstance:
        """단일 부품 인스턴스 생성 (Pure Write)"""
        db_obj = DeviceComponentInstance(**obj_in.model_dump())
        db.add(db_obj)
        db.flush()
        
        audit_command_provider.log_creation(
            db=db, actor_user=actor_user, resource_name="DeviceComponentInstance",
            resource_id=db_obj.id, new_value=db_obj.as_dict()
        )
        return db_obj

    def delete_instance(self, db: Session, *, db_obj: DeviceComponentInstance, actor_user: User) -> None:
        """단일 부품 인스턴스 삭제 (Pure Write)"""
        resource_id = db_obj.id
        deleted_value = db_obj.as_dict()
        
        db.delete(db_obj)
        db.flush()
        
        audit_command_provider.log_deletion(
            db=db, actor_user=actor_user, resource_name="DeviceComponentInstance",
            resource_id=resource_id, deleted_value=deleted_value
        )
    
    def _calculate_rerouted_recipe(
        self, device: DBDevice, recipe: List[BlueprintPinMappingRead], pin_pool: List[int]
    ) -> List[BlueprintPinMappingRead]:
        """
        [Internal Engine] 
        기기의 고장 상태를 확인하여 레시피(설계도)를 실시간으로 교정하는 순수 계산 로직입니다.
        """
        # 1. 현재 기기에서 고장으로 판명된 핀 번호 추출
        faulty_pin_nos = {m.pin_number for m in device.pin_mappings if m.status == PinStatusEnum.FAULTY}
        if not faulty_pin_nos:
            return recipe

        # 2. 레시피에서 이미 사용 중인 핀을 제외하고 가용한 핀 풀 확보
        used_in_recipe = {r.pin_number for r in recipe if r.pin_number is not None}
        available_pins = [p for p in pin_pool if p not in faulty_pin_nos and p not in used_in_recipe]

        # 3. 고장 핀을 발견하면 가용 풀에서 하나씩 꺼내 교체 (우회 실행)
        for item in recipe:
            if item.pin_number in faulty_pin_nos:
                if not available_pins:
                    logger.error(f"❌ 기기 {device.id}: 우회할 가용 핀이 부족합니다.")
                    continue
                item.pin_number = available_pins.pop(0)
        
        return recipe

    def reinitialize_with_smart_rerouting(
        self, db: Session, *, device_obj: DBDevice, raw_recipe: List[BlueprintPinMappingRead], 
        pin_pool: List[int], actor_user: User
    ) -> None:
        """
        [Smart Command] 
        지능형 우회 계산과 물리적 실체화(DB 쓰기)를 한 번에 수행하는 통합 명령입니다.
        Policy는 이 메서드만 호출하면 됩니다.
        """
        # 1. 우회 엔진 가동하여 최종 레시피 산출
        final_recipe = self._calculate_rerouted_recipe(device_obj, raw_recipe, pin_pool)
        
        # 2. 산출된 레시피로 실제 DB 매핑 생성 (기존 메서드 재사용)
        self.reinitialize_components_by_recipe(
            db, device_id=device_obj.id, recipe=final_recipe, actor_user=actor_user
        )
    
    def reroute_faulty_pins(self, db: Session, *, device_obj: DBDevice, pin_pool: List[int], actor_user: User) -> None:
        """
        [The Repairer] 
        이미 설치된 배선 중 고장(FAULTY) 상태인 핀만 찾아 가용 풀에서 대체합니다.
        """
        # 1. 고장 난 매핑들 추출
        faulty_mappings = [m for m in device_obj.pin_mappings if m.status == PinStatusEnum.FAULTY]
        if not faulty_mappings:
            return

        # 2. 현재 사용 중인 핀 번호 제외하고 가용 핀 확보
        used_pins = {m.pin_number for m in device_obj.pin_mappings if m.pin_number is not None}
        available_candidates = [p for p in pin_pool if p not in used_pins]

        # 3. 고장 핀 대체 실행
        for mapping in faulty_mappings:
            if not available_candidates:
                logger.error(f"❌ 기기 {device_obj.id}: 고장 핀 {mapping.pin_name}을 대체할 가용 핀이 없습니다.")
                break
            
            old_pin = mapping.pin_number
            new_pin = available_candidates.pop(0)
            
            mapping.pin_number = new_pin
            # 상태는 그대로 FAULTY로 둘지 ACTIVE로 바꿀지는 정책에 따라 다르나, 
            # 배선이 새로 깔렸으므로 ACTIVE로 복구하는 것이 일반적입니다.
            mapping.status = PinStatusEnum.ACTIVE 

            audit_command_provider.log_event(
                db=db, actor_user=actor_user, 
                event_type="DEVICE_PIN_REROUTED", 
                description=f"Pin {mapping.pin_name} rerouted from {old_pin} to {new_pin}",
                details={"device_id": device_obj.id, "old_pin": old_pin, "new_pin": new_pin}
            )
        
        db.flush()

device_component_instance_command_service = DeviceComponentInstanceCommandService()