import logging
from typing import List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.dependencies import get_db, PermissionChecker, get_current_user
from app.domains.inter_domain.user_identity.schemas.user_identity_command import UserCreate, CompleteRegistration, ContextSwitchRequest
from app.domains.inter_domain.user_identity.schemas.user_identity_query import UserWithToken
from app.core.exceptions import DuplicateEntryError, ValidationError, NotFoundError, AuthenticationError, PermissionDeniedError
from app.domains.inter_domain.policies.authentication.login_policy_provider import login_policy_provider
from app.domains.inter_domain.policies.authentication.registration_policy_provider import registration_policy_provider
from app.domains.inter_domain.policies.authentication.refresh_token_policy_provider import refresh_token_policy_provider
from app.domains.inter_domain.policies.authentication.context_switch_policy_provider import context_switch_policy_provider
from app.core import security
from app.models.objects.user import User as DBUser

router = APIRouter()
logger = logging.getLogger(__name__)

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/login/access-token")
async def login_access_token(
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    The form field "username" is used to receive the user's email.
    """
    form_payload = await request.form()
    raw_username = form_payload.get("username")
    
    try:
        result = await login_policy_provider.login(
            db, email=form_data.username, password=form_data.password, request=request
        )
        db.commit()
        return result
    except AuthenticationError as e:
        db.rollback()
        raise HTTPException(status_code=401, detail=str(e), headers={"WWW-Authenticate": "Bearer", "DPoP-Nonce": security.generate_dpop_nonce()})

@router.post("/login/refresh", status_code=200)
async def refresh_token(
    request: Request,
    *,
    db: Session = Depends(get_db),
    request_in: RefreshTokenRequest
):
    """
    Access Token을 Refresh Token을 사용하여 갱신합니다.
    """
    try:
        result = await refresh_token_policy_provider.execute(
            db=db,
            old_refresh_token=request_in.refresh_token,
            request=request
        )
        db.commit()
        return result
    except HTTPException as e:
        db.rollback()
        raise e
    except AuthenticationError as e:
        db.rollback()
        raise HTTPException(status_code=401, detail=str(e), headers={"WWW-Authenticate": "Bearer"})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.post("/register/initiate")
async def initiate_registration(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate
):
    """
    새로운 사용자 가입 절차를 시작합니다.
    """
    try:
        result = await registration_policy_provider.initiate_registration(db, user_in=user_in)
        return result
    except DuplicateEntryError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.post("/register/complete")
async def complete_registration(
    request: Request,
    *,
    db: Session = Depends(get_db),
    registration_data: CompleteRegistration
):
    """
    제출된 인증 코드를 검증하여 가입 절차를 완료합니다.
    """
    try:
        result = await registration_policy_provider.complete_registration(
            db=db,
            email=registration_data.email,
            verification_code=registration_data.verification_code,
            request=request
        )
        db.commit()
        return result
    except (NotFoundError, ValidationError) as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e), headers={"DPoP-Nonce": security.generate_dpop_nonce()})
    except HTTPException as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@router.post("/context-switch", response_model=UserWithToken)
async def context_switch(
    request: Request,
    *,
    db: Session = Depends(get_db),
    context_switch_req: ContextSwitchRequest,
    user_info: Tuple[DBUser, str, Optional[str]] = Depends(get_current_user)
):
    """
    시스템 관리자가 다른 조직 컨텍스트로 전환하고 해당 조직 ID가 포함된 새 JWT를 발급받습니다.
    """
    current_user, current_user_jwt, dpop_jkt = user_info
    try:
        result = await context_switch_policy_provider.execute(
            db=db,
            current_user_jwt=current_user_jwt,
            target_organization_id=context_switch_req.organization_id,
            request=request,
            dpop_jkt=dpop_jkt
        )
        db.commit()
        return result
    except (PermissionDeniedError, AuthenticationError) as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e), headers={"DPoP-Nonce": security.generate_dpop_nonce()})
    except NotFoundError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e), headers={"DPoP-Nonce": security.generate_dpop_nonce()})
    except HTTPException as e:
        db.rollback()
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")
