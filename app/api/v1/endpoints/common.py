from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.dependencies import get_db, PermissionChecker # PermissionChecker 임포트
from app.domains.inter_domain.user_identity.schemas.user_identity_command import UserCreate, CompleteRegistration
from app.core.exceptions import DuplicateEntryError, ValidationError, NotFoundError, AuthenticationError
# Import providers instead of policies directly
from app.domains.inter_domain.policies.authentication.login_policy_provider import login_policy_provider
from app.domains.inter_domain.policies.authentication.registration_policy_provider import registration_policy_provider
from app.domains.inter_domain.common.schemas.common_query import ManageableResourceResponse, ResourceColumn # 새로 생성한 스키마 임포트

router = APIRouter()

@router.post("/login/access-token")
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    The form field "username" is used to receive the user's email.
    """
    try:
        # Call provider
        result = login_policy_provider.login(
            db, email=form_data.username, password=form_data.password
        )
        db.commit()
        return result
    except AuthenticationError as e:
        db.rollback()
        raise HTTPException(status_code=401, detail=str(e), headers={"WWW-Authenticate": "Bearer"})

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
        # Call provider
        result = await registration_policy_provider.initiate_registration(db, user_in=user_in)
        return result
    except DuplicateEntryError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.post("/register/complete")
def complete_registration(
    *, 
    db: Session = Depends(get_db),
    registration_data: CompleteRegistration
):
    """
    제출된 인증 코드를 검증하여 가입 절차를 완료합니다.
    """
    try:
        # Call provider
        result = registration_policy_provider.complete_registration(
            db, 
            email=registration_data.email, 
            verification_code=registration_data.verification_code
        )
        db.commit()
        return result
    except (NotFoundError, ValidationError) as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.get(
    "/manageable-resources",
    response_model=List[ManageableResourceResponse],
    dependencies=[Depends(PermissionChecker("permission:read"))] # 리소스 메타데이터 조회 권한
)
def get_manageable_resources() -> List[ManageableResourceResponse]:
    """
    ABAC 규칙에서 필터링 대상으로 지정할 수 있는 리소스(테이블) 및 컬럼 메타데이터를 조회합니다.
    """
    # 현재는 프론트엔드 개발을 위해 하드코딩된 목업 데이터를 반환합니다.
    # 실제 데이터베이스 스키마를 기반으로 동적으로 생성되어야 합니다.
    return [
        ManageableResourceResponse(
            resource_name="organization",
            columns=[
                ResourceColumn(name="name", type="string"),
                ResourceColumn(name="country", type="string"),
                ResourceColumn(name="is_active", type="boolean"),
                ResourceColumn(name="created_at", type="datetime"),
            ] # 조직 리소스의 컬럼 예시
        ),
        ManageableResourceResponse(
            resource_name="user",
            columns=[
                ResourceColumn(name="username", type="string"),
                ResourceColumn(name="email", type="string"),
                ResourceColumn(name="is_active", type="boolean"),
            ] # 사용자 리소스의 컬럼 예시
        ),
        ManageableResourceResponse(
            resource_name="device",
            columns=[
                ResourceColumn(name="serial_number", type="string"),
                ResourceColumn(name="is_active", type="boolean"),
            ] # 장치 리소스의 컬럼 예시
        ),
        ManageableResourceResponse(
            resource_name="role",
            columns=[
                ResourceColumn(name="name", type="string"),
                ResourceColumn(name="scope", type="string"),
            ] # 역할 리소스의 컬럼 예시
        ),
        ManageableResourceResponse(
            resource_name="permission",
            columns=[
                ResourceColumn(name="name", type="string"),
            ] # 권한 리소스의 컬럼 예시
        ),
    ]

