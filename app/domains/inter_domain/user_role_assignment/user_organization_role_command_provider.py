from sqlalchemy.orm import Session
from typing import Optional

from app.domains.services.user_identity.crud.user_organization_role_crud import user_organization_role_crud
from app.domains.services.user_identity.schemas.user_identity_command import UserRoleAssignmentCreate, UserRoleAssignmentUpdate
from app.models.relationships.user_organization_role import UserOrganizationRole

class UserOrganizationRoleCommandProvider:
    def create(self, db: Session, *, obj_in: UserRoleAssignmentCreate) -> UserOrganizationRole:
        return user_organization_role_crud.create(db, obj_in=obj_in)

    def update(self, db: Session, *, db_obj: UserOrganizationRole, obj_in: UserRoleAssignmentUpdate) -> UserOrganizationRole:
        return user_organization_role_crud.update(db, db_obj=db_obj, obj_in=obj_in)

    def delete_by_context(self, db: Session, *, user_id: int, organization_id: Optional[int]) -> int:
        return user_organization_role_crud.delete_by_context(db, user_id=user_id, organization_id=organization_id)

user_organization_role_command_provider = UserOrganizationRoleCommandProvider()