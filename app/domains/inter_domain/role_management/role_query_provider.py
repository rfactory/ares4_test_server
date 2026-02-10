from typing import List, Optional
from sqlalchemy.orm import Session

# 서비스는 절대 경로로 import (마이크로서비스 분리 가능성)
from app.domains.services.role_management.services.role_query_service import role_query_service, RoleQueryService
from app.models.objects.user import User
from app.models.objects.role import Role # Role 모델 임포트 추가

# 스키마는 자신의 도메인 내부이므로 상대 경로로 import
from .schemas.role_query import RoleResponse, RolePermissionResponse

class RoleQueryProvider:
    def get_service(self) -> RoleQueryService:
        return role_query_service
    def get_role(self, db: Session, *, role_id: int) -> Optional[Role]:
        """ID로 단일 역할을 조회합니다. 서비스의 결과를 그대로 반환합니다."""
        return role_query_service.get_role(db, role_id=role_id)

    def get_role_by_name(self, db: Session, *, name: str) -> Optional[Role]:
        """이름으로 단일 역할을 조회합니다."""
        return role_query_service.get_role_by_name(db, name=name)

    def get_roles_by_ids(self, db: Session, *, ids: List[int]) -> List[Role]:
        """ID 목록으로 여러 역할을 조회합니다. 서비스의 결과를 그대로 반환합니다."""
        return role_query_service.get_roles_by_ids(db, ids=ids)

    def get_roles_by_organization_id_and_tier(self, db: Session, *, organization_id: int, tier: int) -> List[Role]:
        """조직 ID와 Tier를 기준으로 역할을 조회합니다."""
        return role_query_service.get_roles_by_organization_id_and_tier(db, organization_id=organization_id, tier=tier)

    def get_accessible_roles(self, db: Session, *, actor_user: User, organization_id: int = None) -> List[Role]:
        # 서비스 계층에서 Role 객체를 그대로 반환
        roles = role_query_service.get_accessible_roles(db, actor_user=actor_user, organization_id=organization_id)
        return roles

    def get_permissions_for_role(self, db: Session, *, role_id: int) -> List[RolePermissionResponse]:
        role_permissions = role_query_service.get_permissions_for_role(db, role_id=role_id)
        # RolePermission 객체를 RolePermissionResponse 스키마로 변환합니다.
        # 이때, relationship으로 연결된 permission 객체의 name과 description을 사용합니다.
        return [
            RolePermissionResponse(
                id=rp.id,
                role_id=rp.role_id,
                permission_id=rp.permission_id,
                permission_name=rp.permission.name, # 관계를 통해 이름 가져오기
                permission_description=rp.permission.description, # 관계를 통해 설명 가져오기
                allowed_columns=rp.allowed_columns,
                filter_condition=rp.filter_condition
            )
            for rp in role_permissions
        ]

role_query_provider = RoleQueryProvider()