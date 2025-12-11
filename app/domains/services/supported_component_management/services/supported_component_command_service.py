# services/supported_component_command_service.py

from sqlalchemy.orm import Session

# --- Model Imports ---
from app.models.objects.supported_component import SupportedComponent
from app.models.objects.user import User

# --- CRUD and Schema Imports ---
from ..crud.supported_component_command_crud import supported_component_command_crud
from ..schemas.supported_component_command import SupportedComponentCreate

# --- Provider and Exception Imports ---
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
from app.core.exceptions import DuplicateEntryError

class SupportedComponentCommandService:
    """지원 부품 정보의 생명주기를 관리합니다."""

    def create_supported_component(self, db: Session, *, obj_in: SupportedComponentCreate, actor_user: User) -> SupportedComponent:
        """
        새로운 종류의 지원 부품을 시스템에 등록합니다.
        """
        # 방어적 확인: component_type 중복 확인
        existing_supported_component = db.query(SupportedComponent).filter(SupportedComponent.component_type == obj_in.component_type).first()
        if existing_supported_component:
            raise DuplicateEntryError(resource_name="SupportedComponent", field_name="component_type", field_value=obj_in.component_type)

        new_component = supported_component_command_crud.create(db, obj_in=obj_in)
        db.flush() # ID 발급을 위해 flush

        audit_command_provider.log_creation(
            db=db,
            actor_user=actor_user,
            resource_name="SupportedComponent",
            resource_id=new_component.id,
            new_value=new_component.as_dict()
        )
        return new_component

supported_component_command_service = SupportedComponentCommandService()
