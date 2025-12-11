from app.core.crud_base import CRUDBase
from app.models.objects.role import Role
from ..schemas.role_command import RoleCreate, RoleUpdate

class CRUDRoleCommand(CRUDBase[Role, RoleCreate, RoleUpdate]):
    pass

role_command_crud = CRUDRoleCommand(model=Role)
