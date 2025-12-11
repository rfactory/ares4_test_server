# C:\vscode project files\Ares4\server2\app\domains\services\organizations\services\organization_command_service.py
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateEntryError, NotFoundError
from app.models.objects.organization import Organization, OrganizationType
from app.models.objects.user import User
from ..crud.organization_command_crud import organization_crud_command
from ..crud.organization_query_crud import organization_crud_query # Check for duplicates
from ..schemas.organization_command import OrganizationCreate, OrganizationUpdate
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider


class OrganizationCommandService:
    """
    조직(Organization) 정보에 대한 생성, 수정, 삭제 등 'Command' 성격의 비즈니스 로직을 담당합니다.
    모든 데이터 변경 작업에 대해 감사 로그(Audit Log)를 기록합니다.
    """
    def create_organization(self, db: Session, *, org_in: OrganizationCreate, actor_user: User) -> Organization:
        """
        새로운 조직을 생성합니다.
        - 비즈니스 로직: 중복된 사업자 등록 번호가 있는지 확인합니다. (향후 Policy/Validator로 이동 권장)
        - 방어적 확인: 조직 유형 ID가 유효한지 확인합니다.
        - 조직을 생성하고, 감사 로그를 기록합니다.
        """
        # 방어적 확인
        if not db.query(OrganizationType).filter(OrganizationType.id == org_in.organization_type_id).first():
            raise NotFoundError("OrganizationType", str(org_in.organization_type_id))

        # 비즈니스 로직 (Policy/Validator로 이동 필요)
        existing_org = organization_crud_query.get_by_registration_number(db, registration_number=org_in.business_registration_number)
        if existing_org:
            raise DuplicateEntryError("Organization", "business_registration_number", org_in.business_registration_number)
        
        new_org = organization_crud_command.create(db, obj_in=org_in)
        db.flush()  # ← ID 생성 보장

        audit_command_provider.log_creation(
            db=db,
            actor_user=actor_user,
            resource_name="Organization",
            resource_id=new_org.id,
            new_value=new_org.as_dict()
        )
        return new_org  # ← commit 없음! Policy에서 할 거임

    def update_organization(self, db: Session, *, org_id: int, org_in: OrganizationUpdate, actor_user: User) -> Organization:
        """
        기존 조직 정보를 수정합니다.
        """
        org_to_update = organization_crud_query.get(db, id=org_id)
        if not org_to_update:
            raise NotFoundError(resource_name="Organization", resource_id=str(org_id))
        
        # 방어적 확인
        if org_in.organization_type_id is not None:
            if not db.query(OrganizationType).filter(OrganizationType.id == org_in.organization_type_id).first():
                raise NotFoundError("OrganizationType", str(org_in.organization_type_id))

        old_value = org_to_update.as_dict()
        
        updated_org = organization_crud_command.update(db, db_obj=org_to_update, obj_in=org_in)
        db.flush()  # ← 필요시만

        audit_command_provider.log_update(
            db=db,
            actor_user=actor_user,
            resource_name="Organization",
            resource_id=updated_org.id,
            old_value=old_value,
            new_value=updated_org.as_dict()
        )
        return updated_org

    def delete_organization(self, db: Session, *, org_id: int, actor_user: User) -> Organization:
        """
        조직을 삭제합니다. (Soft-delete 아님)
        """
        org_to_delete = organization_crud_query.get(db, id=org_id)
        if not org_to_delete:
            raise NotFoundError(resource_name="Organization", resource_id=str(org_id))
        
        deleted_value = org_to_delete.as_dict()
        
        deleted_org = organization_crud_command.remove(db, id=org_id)
        db.flush() # ← 필요한 경우 (e.g., deleted_org.id가 audit log에 사용될 때)

        audit_command_provider.log_deletion(
            db=db,
            actor_user=actor_user,
            resource_name="Organization",
            resource_id=org_id,
            deleted_value=deleted_value
        )
        return deleted_org

organization_command_service = OrganizationCommandService()
