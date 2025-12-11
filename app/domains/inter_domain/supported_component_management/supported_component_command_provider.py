# inter_domain/supported_component_management/supported_component_command_provider.py

from sqlalchemy.orm import Session

# --- Service Imports ---
from app.domains.services.supported_component_management.services.supported_component_command_service import supported_component_command_service

# --- Schema and Model Imports ---
from app.domains.services.supported_component_management.schemas.supported_component_command import SupportedComponentCreate
from app.models.objects.supported_component import SupportedComponent
from app.models.objects.user import User

class SupportedComponentCommandProvider:
    """
    지원 부품(Supported Component) 관련 Command 서비스의 기능을 외부 도메인에 노출하는 제공자입니다.
    """
    def create_supported_component(self, db: Session, *, obj_in: SupportedComponentCreate, actor_user: User) -> SupportedComponent:
        return supported_component_command_service.create_supported_component(db=db, obj_in=obj_in, actor_user=actor_user)

supported_component_command_provider = SupportedComponentCommandProvider()
