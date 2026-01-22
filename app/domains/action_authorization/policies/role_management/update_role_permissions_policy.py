import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.objects.user import User
from app.models.objects.role import Role
from app.models.objects.permission import Permission
from app.domains.inter_domain.role_management.schemas.role_command import PermissionAssignment
from app.domains.inter_domain.role_management.role_query_provider import role_query_provider
from app.domains.inter_domain.validators.permission.locked_permission_validator_provider import locked_permission_validator_provider

class UpdateRolePermissionsPolicy:
    def execute(
        self, 
        db: Session, 
        *, 
        actor_user: User, 
        target_role_id: int, 
        permissions_in: List[PermissionAssignment],
        x_organization_id: Optional[int]
    ) -> None:
        """
        역할 권한 업데이트를 위한 정책을 실행합니다. (핵심 안전 장치 로직 구현)
        """
        # 1. 대상 역할 조회
        target_role = db.query(Role).options(joinedload(Role.permissions)).filter(Role.id == target_role_id).first()
        if not target_role:
            raise NotFoundError("Role", str(target_role_id))

        # 2. 규칙: 보호된 역할 (tier 0, 1) 수정 금지
        if target_role.tier is not None and target_role.tier < 2:
            raise PermissionDeniedError(f"Permissions for protected role '{target_role.name}' (tier {target_role.tier}) cannot be modified.")
        
        # 3. 규칙: 조직 교차 접근 방지
        if target_role.scope == "ORGANIZATION" and target_role.organization_id != x_organization_id:
            raise PermissionDeniedError("You cannot modify roles outside your current organization context.")

        # 4. 규칙: 시스템 잠금 권한 수정/제거 방지 (신규)
        current_permission_ids = {rp.permission_id for rp in target_role.permissions}
        requested_permission_ids = {p.permission_id for p in permissions_in}
        
        changed_ids = current_permission_ids.symmetric_difference(requested_permission_ids)
        if changed_ids:
            changed_permissions = db.query(Permission).filter(Permission.id.in_(changed_ids)).all()
            locked_permission_validator_provider.validate(changed_permissions=changed_permissions)

        # 5. 규칙: 권한 상속의 부분집합 원칙 (자신이 가지지 않은 권한은 부여할 수 없다)
        actor_permissions_set = set()
        for assignment in actor_user.user_role_assignments:
            is_system_context_permission = assignment.role.scope == 'SYSTEM'
            is_current_org_context_permission = assignment.role.scope == 'ORGANIZATION' and assignment.organization_id == x_organization_id
            
            if is_system_context_permission or is_current_org_context_permission:
                for rp in assignment.role.permissions:
                    actor_permissions_set.add(rp.permission.name)

        # 4b. 요청된 permission_id 목록을 permission_name으로 변환
        requested_permission_ids = [p.permission_id for p in permissions_in]
        if not requested_permission_ids:
            return
            
        permissions_from_db = db.query(Permission).filter(Permission.id.in_(requested_permission_ids)).all()
        if len(permissions_from_db) != len(requested_permission_ids):
            raise NotFoundError("Permission", "One or more requested permission IDs do not exist.")
        
        requested_permission_names_set = {p.name for p in permissions_from_db}

        # 4c. 요청된 권한이 요청자 권한의 부분집합인지 확인
        if not requested_permission_names_set.issubset(actor_permissions_set):
            missing_perms = requested_permission_names_set - actor_permissions_set
            raise PermissionDeniedError(f"You cannot grant permissions you do not possess: {', '.join(missing_perms)}")

update_role_permissions_policy = UpdateRolePermissionsPolicy()
