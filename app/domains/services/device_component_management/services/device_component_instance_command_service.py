import logging
from sqlalchemy.orm import Session
from typing import List

# --- Model Imports ---
from app.models.relationships.device_component_instance import DeviceComponentInstance
from app.models.relationships.device_component_pin_mapping import DeviceComponentPinMapping, PinStatusEnum
from app.models.objects.user import User

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

device_component_instance_command_service = DeviceComponentInstanceCommandService()