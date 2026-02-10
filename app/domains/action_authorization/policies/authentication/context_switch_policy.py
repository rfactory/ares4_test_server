from sqlalchemy.orm import Session
from fastapi import Request, HTTPException, status
from datetime import timedelta
from typing import Optional

from app.core.security import create_access_token, verify_access_token
from app.domains.inter_domain.user_identity.schemas.user_identity_query import UserWithToken, User
from app.domains.inter_domain.user_identity.user_identity_query_provider import user_identity_query_provider
from app.domains.inter_domain.organizations.organization_query_provider import organization_query_provider # 추가
from app.domains.inter_domain.permissions.permission_query_provider import permission_query_provider # 추가
from app.core.config import settings
from app.core.exceptions import PermissionDeniedError, NotFoundError
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

class ContextSwitchPolicy(object):
    async def execute(
        self,
        db: Session,
        *,
        current_user_jwt: str, # 현재 사용자의 JWT를 받음 (클레임 추출용)
        target_organization_id: int,
        request: Request, # For DPoP
        dpop_jkt: Optional[str] = None # DPoP jkt 추가
    ) -> UserWithToken:
        # 1. 현재 사용자 ID 추출 및 권한 확인
        current_user_payload = verify_access_token(token=current_user_jwt, dpop_jkt=dpop_jkt)
        current_user_id = current_user_payload.id

        current_user = user_identity_query_provider.get_user_by_id(db, user_id=current_user_id)
        if not current_user:
            raise NotFoundError("Current user not found.")

        # 2. [수정] system:context_switch 권한 확인
        # user_identity_query_provider에 없는 has_permission 대신 permission_query_provider를 사용합니다.
        user_permissions = permission_query_provider.get_permissions_for_user_in_context(
            db, 
            user_id=current_user_id, 
            organization_id=None # SYSTEM 컨텍스트에서 권한 확인
        )
        
        if "system:context_switch" not in user_permissions:
            raise PermissionDeniedError("Not authorized to switch context to an organization.")

        # 3. 대상 조직의 존재 여부 확인 (필수)
        target_org = organization_query_provider.get_organization_by_id(db, org_id=target_organization_id)
        if not target_org:
            raise NotFoundError("Target organization not found.")

        # 4. 새로운 Access Token 생성 (temp_org_id 클레임 포함)
        access_token_expires = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        
        # 새로운 JWT 클레임에 조직 ID 추가
        data = {"sub": str(current_user.id), "temp_org_id": target_organization_id}
        new_access_token = create_access_token(data, dpop_jkt=dpop_jkt, expires_delta=timedelta(minutes=access_token_expires))
        
        # 5. 감사 로그 기록
        audit_command_provider.log(
            db=db,
            event_type="CONTEXT_SWITCHED",
            description=f"User {current_user.username} switched context to Org ID: {target_organization_id}",
            actor_user=current_user,
            details={
                "target_org_id": target_organization_id,
                "previous_org_id": current_user_payload.temp_org_id if hasattr(current_user_payload, 'temp_org_id') else None
            }
        )
        
        # 6. 트랜잭션 커밋
        db.commit()
        
        # 7. UserWithToken 형식으로 반환
        return UserWithToken(
            user=current_user, # UserWithToken 스키마에 맞는 User 객체
            token={"access_token": new_access_token, "token_type": "bearer"}
        )

context_switch_policy = ContextSwitchPolicy()