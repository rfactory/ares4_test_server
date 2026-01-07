from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_db, get_current_user, PermissionChecker
from app.models.objects.user import User
from app.core.exceptions import NotFoundError, AppLogicError

# 스키마 및 프로바이더 임포트
from app.domains.inter_domain.access_requests.access_requests_query_provider import access_request_query_provider
from app.domains.inter_domain.policies.access_requests.approve_request_policy_provider import approve_request_policy_provider
from app.domains.inter_domain.policies.access_requests.reject_request_policy_provider import reject_request_policy_provider
from app.domains.services.access_requests.schemas.access_request_query import AccessRequestRead

router = APIRouter()

@router.get("/upgrade-requests", response_model=List[AccessRequestRead])
def get_pending_upgrade_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _permission: None = Depends(PermissionChecker("admin:requests:read")) 
):
    """
    보류 중인 모든 접근 요청(가입/승격) 목록을 조회합니다.
    """
    access_requests = access_request_query_provider.get_pending_requests_for_actor(
        db, actor_user=current_user, organization_id=None
    )
    return access_requests

@router.post("/upgrade-requests/{request_id}/approve", response_model=AccessRequestRead)
def approve_upgrade_request(
    *, 
    db: Session = Depends(get_db),
    request_id: int = Path(..., title="The ID of the access request to approve"),
    current_user: User = Depends(get_current_user),
    _permission: None = Depends(PermissionChecker("admin:requests:approve"))
):
    """
    접근 요청을 승인합니다. 승인 시, 역할을 바로 부여하지 않고 인증 코드를 발송합니다.
    """
    try:
        updated_request = approve_request_policy_provider.execute(
            db=db, request_id=request_id, admin_user=current_user
        )
        return updated_request
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AppLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

@router.post("/upgrade-requests/{request_id}/reject", response_model=AccessRequestRead)
def reject_upgrade_request(
    *, 
    db: Session = Depends(get_db),
    request_id: int = Path(..., title="The ID of the access request to reject"),
    current_user: User = Depends(get_current_user),
    _permission: None = Depends(PermissionChecker("admin:requests:reject"))
):
    """
    접근 요청을 거부합니다.
    """
    try:
        updated_request = reject_request_policy_provider.execute(
            db=db, request_id=request_id, admin_user=current_user
        )
        return updated_request
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AppLogicError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")
