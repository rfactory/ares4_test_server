from sqlalchemy.orm import Session

from app.models.objects.organization import Organization
from app.models.objects.organization_type import OrganizationType
from app.models.objects.user import User
from ..crud.organization_command_crud import organization_crud_command
from ..crud.organization_type_query_crud import organization_type_crud_query
from ..crud.organization_type_command_crud import organization_type_crud_command, OrganizationTypeCreate
from ..schemas.organization_command import OrganizationCreate, OrganizationUpdate
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
# 역할 삭제를 위한 임포트 추가
from app.domains.services.role_management.crud.role_query_crud import role_query_crud
from app.domains.services.role_management.crud.role_command_crud import role_command_crud

class OrganizationCommandService:
    """
    조직(Organization) 정보에 대한 생성, 수정, 삭제 등 'Command' 성격의 비즈니스 로직을 담당합니다.
    """
    def find_or_create_organization_type(self, db: Session, *, name: str) -> OrganizationType:
        """조직 유형을 이름으로 찾거나, 없으면 새로 생성합니다."""
        org_type = organization_type_crud_query.get_by_name(db, name=name)
        if org_type:
            return org_type
        
        new_org_type_schema = OrganizationTypeCreate(name=name, description=f"Dynamically created type: {name}")
        new_org_type = organization_type_crud_command.create(db, obj_in=new_org_type_schema)
        return new_org_type

    def create_organization_type(self, db: Session, *, org_type_in: OrganizationTypeCreate) -> OrganizationType:
        """새로운 조직 유형을 생성합니다."""
        new_org_type = organization_type_crud_command.create(db, obj_in=org_type_in)
        return new_org_type

    def create_organization(self, db: Session, *, org_in: OrganizationCreate, actor_user: User) -> Organization:
        """
        새로운 조직을 생성합니다.
        """
        new_org = organization_crud_command.create(db, obj_in=org_in)
        db.flush()  # ID 생성 보장

        audit_command_provider.log(
            db=db,
            actor_user=actor_user,
            event_type="ORGANIZATION_CREATED",
            description=f"Organization '{new_org.company_name}' created.",
            details={"new_value": new_org.as_dict()}
        )
        return new_org

    def update_organization(self, db: Session, *, org_to_update: Organization, org_in: OrganizationUpdate, actor_user: User) -> Organization:
        """
        기존 조직 정보를 수정합니다.
        """
        old_value = org_to_update.as_dict()
        
        updated_org = organization_crud_command.update(db, db_obj=org_to_update, obj_in=org_in)
        db.flush()

        audit_command_provider.log(
            db=db,
            actor_user=actor_user,
            event_type="ORGANIZATION_UPDATED",
            description=f"Organization '{updated_org.company_name}' updated.",
            details={"old_value": old_value, "new_value": updated_org.as_dict()}
        )
        return updated_org

    def delete_organization(self, db: Session, *, org_to_delete: Organization, actor_user: User) -> Organization:
        """
        조직을 삭제하고, 해당 조직에 속한 모든 역할도 함께 삭제합니다.
        """
        deleted_value = org_to_delete.as_dict()
        org_id = org_to_delete.id
        org_name = org_to_delete.company_name

        # 1. 이 조직에 속한 모든 역할 조회
        roles_to_delete = role_query_crud.get_roles_by_organization_id(db, organization_id=org_id)

        # 2. 조회된 역할들 삭제
        for role in roles_to_delete:
            # 참고: 이 로직은 역할이 사용 중일 경우 실패할 수 있음. 
            # 상위 정책 계층에서 조직 삭제 전, 조직 내 사용자가 모두 없는지 등을 확인해야 함.
            role_command_crud.remove(db, id=role.id)

        # 3. 조직 삭제
        deleted_org = organization_crud_command.remove(db, id=org_id)
        db.flush()

        # 4. 감사 로그 기록
        audit_command_provider.log(
            db=db,
            actor_user=actor_user,
            event_type="ORGANIZATION_DELETED",
            description=f"Organization '{org_name}' (ID: {org_id}) and all associated roles deleted.",
            details={"deleted_value": deleted_value}
        )
        return deleted_org

organization_command_service = OrganizationCommandService()
