# crud/supported_component_command_crud.py
from app.core.crud_base import CRUDBase
from app.models.objects.supported_component import SupportedComponent
from ..schemas.supported_component_command import SupportedComponentCreate, SupportedComponentUpdate

class CRUDSupportedComponentCommand(CRUDBase[SupportedComponent, SupportedComponentCreate, SupportedComponentUpdate]):
    """지원 부품 정보의 생성, 수정, 삭제를 담당합니다."""
    pass

supported_component_command_crud = CRUDSupportedComponentCommand(SupportedComponent)
