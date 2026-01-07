from app.core.crud_base import CRUDBase
from app.models.objects.organization_type import OrganizationType
# 스키마를 올바른 위치에서 import 합니다.
from ..schemas.organization_command import OrganizationTypeCreate

class CRUDOrganizationTypeCommand(CRUDBase[OrganizationType, OrganizationTypeCreate, None]):
    # OrganizationType은 생성만 필요하므로, Update 스키마는 None으로 지정합니다.
    pass

organization_type_crud_command = CRUDOrganizationTypeCommand(model=OrganizationType)
