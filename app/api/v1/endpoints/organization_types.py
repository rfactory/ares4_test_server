# C:\vscode project files\Ares4\server2\app\api\v1\endpoints\organization_types.py

from typing import List, Tuple, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, PermissionChecker
from app.models.objects.user import User
from app.domains.inter_domain.organizations.organization_query_provider import organization_query_provider
# 정책 프로바이더 임포트 (기존 organization_command_provider는 삭제해도 됩니다)
from app.domains.inter_domain.policies.organization_management.create_organization_type_policy_provider import create_organization_type_policy_provider
from app.domains.inter_domain.organizations.schemas.organization_query import OrganizationTypeResponse
from app.domains.inter_domain.organizations.schemas.organization_command import OrganizationTypeCreate
from app.core.exceptions import DuplicateEntryError

router = APIRouter()

@router.get("", response_model=List[OrganizationTypeResponse])
async def get_organization_types(
    db: Session = Depends(get_db),
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    """
    모든 조직 유형의 목록을 조회합니다. (조회는 Query Provider를 통해 직접 수행)
    """
    current_user, _, _ = user_info
    return organization_query_provider.get_organization_types(db, skip=skip, limit=limit)

@router.post("", response_model=OrganizationTypeResponse)
async def create_organization_type(
    *,
    db: Session = Depends(get_db),
    org_type_in: OrganizationTypeCreate,
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user),
    _permission: None = Depends(PermissionChecker("organization_type:create"))
):
    """
    새로운 조직 유형을 생성합니다.
    (Ares Aegis: 전용 정책 프로바이더를 통해 트랜잭션 및 감사 로그를 완결함)
    """
    current_user, _, _ = user_info
    try:
        # 정책 지휘관에게 한 줄로 명령 하달
        return create_organization_type_policy_provider.execute(
            db, org_type_in=org_type_in, actor_user=current_user
        )
    except DuplicateEntryError as e:
        # 정책 내부에서 이미 rollback이 수행되었습니다.
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")