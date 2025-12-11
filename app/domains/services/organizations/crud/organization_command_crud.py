# C:\vscode project files\Ares4\server2\app\domains\services\organizations\crud\organization_command_crud.py
from app.core.crud_base import CRUDBase
from app.models.objects.organization import Organization
from ..schemas.organization_command import OrganizationCreate, OrganizationUpdate

# --- Command-related CRUD --- 
# 이 파일은 데이터의 상태를 변경하는 DB 작업을 직접 수행하는 'Command' CRUD 클래스를 정의합니다.

class CRUDOrganizationCommand(CRUDBase[Organization, OrganizationCreate, OrganizationUpdate]):
    """
    조직(Organization) 정보에 대한 생성(Create), 수정(Update), 삭제(Delete) DB 작업을 담당합니다.
    CRUDBase를 상속받아 기본적인 CUD 메서드를 제공받습니다.
    """
    pass

organization_crud_command = CRUDOrganizationCommand(Organization)
