import logging
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Tuple

from app.dependencies import get_db, get_current_user, PermissionChecker
from app.models.objects.user import User
from app.core.exceptions import NotFoundError, AppLogicError
from app.domains.inter_domain.policies.access_requests.create_join_request_policy_provider import create_join_request_policy_provider
from app.domains.inter_domain.access_requests.schemas.access_request_command import AccessRequestInvite, AcceptInvitationRequest
from app.domains.inter_domain.access_requests.schemas.access_request_query import AccessRequestRead
from app.domains.inter_domain.policies.access_requests.create_invitation_policy_provider import create_invitation_policy_provider
from app.domains.inter_domain.policies.access_requests.accept_invitation_policy_provider import accept_invitation_policy_provider
from app.domains.inter_domain.access_requests.access_requests_query_provider import access_request_query_provider


# 요청 본문을 위한 스키마 정의
class JoinRequestCreate(BaseModel):
    org_identifier: str
    reason: str | None = None

router = APIRouter()


@router.get("", response_model=List[AccessRequestRead])
async def get_pending_requests(
    *,
    db: Session = Depends(get_db),
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user),
    organization_id: Optional[int] = Header(None, alias="X-Organization-ID"),
    _ = Depends(PermissionChecker(required_permission="access-request:read"))
):
    """
    현재 사용자의 컨텍스트에 따라 보류 중인 접근 요청 목록을 가져옵니다.
    """
    current_user, _, _ = user_info
    return access_request_query_provider.get_pending_requests_for_actor(
        db=db, actor_user=current_user, organization_id=organization_id
    )


@router.post("/join", status_code=status.HTTP_202_ACCEPTED)
async def request_to_join_organization(
    *,
    db: Session = Depends(get_db),
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user),
    request_in: JoinRequestCreate
):
    """
    사용자가 특정 조직에 가입 요청을 보냅니다.
    """
    current_user, _, _ = user_info
    try:
        create_join_request_policy_provider.execute(
            db=db,
            requester_user=current_user,
            org_identifier=request_in.org_identifier,
            reason=request_in.reason
        )
        return {"message": "Request to join has been submitted successfully."}

    except (NotFoundError, AppLogicError) as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.post("/invite", status_code=status.HTTP_202_ACCEPTED)
async def invite_user(
    *,
    db: Session = Depends(get_db),
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user),
    invitation_in: AccessRequestInvite,
    _ = Depends(PermissionChecker(required_permission="role:read")) 
):
    """
    관리자가 사용자를 특정 역할에 초대합니다. (Push Model)
    """
    actor_user, _, _ = user_info
    # Policy에서 발생하는 모든 비즈니스 예외는 main.py의 전역 처리기가 처리합니다.
    result = await create_invitation_policy_provider.execute(
        db=db,
        actor_user=actor_user,
        invitation_in=invitation_in
    )
    return result


@router.post("/accept", status_code=status.HTTP_200_OK)
async def accept_invitation(
    *,
    db: Session = Depends(get_db),
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user),
    request_in: AcceptInvitationRequest
):
    """
    사용자가 인증 코드를 사용하여 초대를 수락합니다.
    """
    current_user, _, _ = user_info
    # Policy에서 발생하는 모든 비즈니스 예외는 main.py의 전역 처리기가 처리합니다.
    result = await accept_invitation_policy_provider.execute(
        db=db,
        accepting_user=current_user,
        verification_code=request_in.verification_code
    )
    return result