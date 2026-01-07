from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.objects.role import Role
from app.models.objects.user import User
from app.models.relationships.role_permission import RolePermission # RolePermission 모델 임포트
from ..crud.role_query_crud import role_query_crud
from ..crud.role_permission_query_crud import role_permission_query_crud # 새로운 CRUD 임포트

class RoleQueryService:
    def get_role(self, db: Session, *, role_id: int) -> Optional[Role]:
        """ID로 역할을 조회합니다."""
        return role_query_crud.get(db, id=role_id)

    def get_roles_by_ids(self, db: Session, *, ids: List[int]) -> List[Role]:
        """ID 목록으로 여러 역할을 조회합니다."""
        return role_query_crud.get_multi_by_ids(db, ids=ids)

    def get_roles_by_organization_id_and_tier(self, db: Session, *, organization_id: int, tier: int) -> List[Role]:
        """조직 ID와 Tier를 기준으로 역할을 조회합니다."""
        return role_query_crud.get_roles_by_organization_id_and_tier(db, organization_id=organization_id, tier=tier)

    def get_role_by_name(self, db: Session, *, name: str) -> Optional[Role]:
        """이름으로 역할을 조회합니다."""
        return role_query_crud.get_by_name(db, name=name)

    def get_all_roles(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Role]:
        """모든 역할을 조회합니다."""
        return role_query_crud.get_multi(db, skip=skip, limit=limit)

    def get_accessible_roles(self, db: Session, *, actor_user: User, organization_id: int = None) -> List[Role]:
        """
        요청한 사용자가 접근할 수 있는 역할 목록을 반환합니다.
        - 시스템 관리자는 모든 SYSTEM 역할 목록을 봅니다.
        - 조직 관리자는 해당 조직의 역할 목록만 봅니다.
        """
        if organization_id:
            # 조직 컨텍스트에서 조회하는 경우, 해당 조직의 역할만 반환
            # TODO: 엔드포인트 레벨에서 요청한 사용자가 이 organization_id에 대해 관리 권한이 있는지 확인해야 함.
            return role_query_crud.get_roles_by_organization_id(db, organization_id=organization_id)
        else:
            # 시스템 컨텍스트에서 조회하는 경우, SYSTEM 스코프의 역할만 반환
            # TODO: 엔드포인트 레벨에서 요청한 사용자가 SYSTEM 스코프에 대해 관리 권한이 있는지 확인해야 함.
            return role_query_crud.get_roles_by_scope(db, scope='SYSTEM')

    def get_permissions_for_role(self, db: Session, *, role_id: int) -> List[RolePermission]:
        """특정 역할에 할당된 모든 권한 관계를 조회합니다."""
        return role_permission_query_crud.get_by_role_id(db, role_id=role_id)

role_query_service = RoleQueryService()
