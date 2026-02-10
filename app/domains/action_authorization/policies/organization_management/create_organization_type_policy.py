import logging
from sqlalchemy.orm import Session
from app.models.objects.user import User
from app.domains.inter_domain.organizations.organization_command_provider import organization_command_provider
from app.domains.inter_domain.organizations.schemas.organization_command import OrganizationTypeCreate
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
from app.core.exceptions import DuplicateEntryError

logger = logging.getLogger(__name__)

class CreateOrganizationTypePolicy:
    def execute(self, db: Session, *, org_type_in: OrganizationTypeCreate, actor_user: User):
        try:
            # 1. 조직 유형 생성 수행 (Command Service 호출)
            new_org_type = organization_command_provider.create_organization_type(db, org_type_in=org_type_in)
            
            # [Ares Aegis] 2. 시스템 감사 로그 기록
            audit_command_provider.log(
                db=db,
                event_type="ORG_TYPE_CREATED",
                description=f"New organization type defined: {org_type_in.name}",
                actor_user=actor_user,
                details={"type_name": org_type_in.name}
            )

            # 3. 트랜잭션 최종 확정 및 객체 갱신
            db.commit()
            db.refresh(new_org_type)
            return new_org_type

        except DuplicateEntryError as e:
            db.rollback()
            raise e
        except Exception as e:
            db.rollback()
            logger.error(f"Critical failure in CreateOrganizationTypePolicy: {e}")
            raise e

create_organization_type_policy = CreateOrganizationTypePolicy()