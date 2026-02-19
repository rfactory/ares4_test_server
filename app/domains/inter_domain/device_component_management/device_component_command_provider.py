from sqlalchemy.orm import Session
from typing import List

# --- Service Imports ---
from app.domains.services.device_component_management.services.device_component_instance_command_service import device_component_instance_command_service

# --- Schema and Model Imports ---
from app.domains.services.hardware_blueprint.schemas.hardware_blueprint_query import BlueprintPinMappingRead
from app.models.relationships.device_component_instance import DeviceComponentInstance
from app.models.objects.user import User

class DeviceComponentCommandProvider:
    """
    [Inter-Domain Provider]
    기기 부품 도메인의 실행 명령을 외부(Policy)로 노출합니다.
    """

    def reinitialize_components_by_recipe(
        self, 
        db: Session, 
        *, 
        device_id: int, 
        recipe: List[BlueprintPinMappingRead], 
        actor_user: User
    ) -> None:
        """
        Policy가 전달한 회로도 레시피를 바탕으로 기기의 핀 배선을 실체화합니다.
        기존의 개별 부품 연결 방식을 대체하여 전체 핀맵을 한 번에 구성합니다.
        """
        return device_component_instance_command_service.reinitialize_components_by_recipe(
            db=db, 
            device_id=device_id, 
            recipe=recipe, 
            actor_user=actor_user
        )

    def delete_instance(self, db: Session, *, db_obj: DeviceComponentInstance, actor_user: User) -> None:
        """단일 부품 인스턴스를 제거하는 순수 명령 통로입니다."""
        return device_component_instance_command_service.delete_instance(
            db=db, 
            db_obj=db_obj, 
            actor_user=actor_user
        )

device_component_command_provider = DeviceComponentCommandProvider()