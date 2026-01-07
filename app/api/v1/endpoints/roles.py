from typing import List, Optional
from fastapi import APIRouter, Depends, Header, Path, HTTPException, status, Body
from sqlalchemy.orm import Session

# 애플리케이션 핵심 종속성 임포트
from app.dependencies import get_db, get_current_user, PermissionChecker
# 사용자 정의 예외 임포트: API 로직에서 발생하는 특정 오류 처리
from app.core.exceptions import PermissionDeniedError, NotFoundError, DuplicateEntryError, ForbiddenError, ConflictError

# 역할(Role) 관리 관련 스키마 및 프로바이더 임포트
# - role_query: 역할을 조회할 때 사용되는 응답 스키마
# - role_command: 역할을 생성, 수정할 때 사용되는 요청 스키마
# - role_query_provider: 역할 조회 비즈니스 로직을 캡슐화한 프로바이더
# - role_command_provider: 역할 생성, 수정, 삭제 비즈니스 로직을 캡슐화한 프로바이더
from app.domains.inter_domain.role_management.schemas.role_query import RoleResponse, RolePermissionResponse
from app.domains.inter_domain.role_management.schemas.role_command import RolePermissionUpdateRequest, RoleCreate, RoleUpdate
from app.domains.inter_domain.role_management.role_query_provider import role_query_provider
from app.domains.inter_domain.role_management.role_command_provider import role_command_provider

# 역할 권한 업데이트 시 적용되는 정책 프로바이더 임포트
# - 이 정책은 UI를 통한 중요 역할(예: SUPER_ADMIN) 수정 방지, 권한 상속 규칙 준수 등 핵심 안전 장치 로직을 담당
from app.domains.inter_domain.policies.role_management.update_role_permissions_policy_provider import update_role_permissions_policy_provider
from app.domains.inter_domain.policies.role_management.create_role_policy_provider import create_role_policy_provider
from app.domains.inter_domain.policies.role_management.delete_role_policy_provider import delete_role_policy_provider # 삭제 정책 추가
from app.domains.inter_domain.policies.role_management.update_role_policy_provider import update_role_policy_provider # 수정 정책 추가

# SQLAlchemy ORM 모델 임포트: 타입 힌팅 및 종속성 주입에 사용
from app.models.objects.user import User

# FastAPI 라우터 인스턴스 생성
router = APIRouter()


# --- 역할 생성 API ---
@router.post(
    "/",
    response_model=RoleResponse, # 성공 시 반환될 데이터 모델
    status_code=status.HTTP_201_CREATED, # 성공 시 HTTP 201 상태 코드 반환
    dependencies=[Depends(PermissionChecker("role:create"))] # 'role:create' 권한이 있는 사용자만 접근 가능
)
def create_role(
    db: Session = Depends(get_db), # 데이터베이스 세션 종속성 주입
    current_user: User = Depends(get_current_user), # 현재 로그인한 사용자 정보 주입
    role_in: RoleCreate = Body(...), # 요청 본문으로부터 RoleCreate 스키마 데이터 파싱
    x_organization_id: Optional[int] = Header(None, alias="X-Organization-ID") # HTTP 헤더에서 조직 ID 추출
) -> RoleResponse:
    """
    새로운 역할을 생성합니다.
    
    - **권한:** `role:create` 권한이 필요합니다.
    - **요청 본문:** `RoleCreate` 스키마에 정의된 역할 정보를 포함해야 합니다.
    - **응답:** 새로 생성된 역할의 `RoleResponse` 스키마 데이터를 반환합니다.
    - **예외:**
        - `DuplicateEntryError` (409 Conflict): 이미 동일한 이름의 역할이 존재하는 경우.
        - `HTTPException` (500 Internal Server Error): 예상치 못한 서버 오류 발생 시.
    """
    try:
        create_role_policy_provider.execute(
            db,
            actor_user=current_user,
            role_in=role_in,
            x_organization_id=x_organization_id
        )

        new_role = role_command_provider.create_role(db, role_in=role_in, actor_user=current_user)
        db.commit()
        return new_role
    except DuplicateEntryError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))
    except ForbiddenError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


# --- 역할 목록 조회 API ---
@router.get(
    "/",
    response_model=List[RoleResponse], # 성공 시 반환될 데이터 모델 목록
    dependencies=[Depends(PermissionChecker("role:read"))] # 'role:read' 권한이 있는 사용자만 접근 가능
)
def get_roles(
    db: Session = Depends(get_db), # 데이터베이스 세션 종속성 주입
    current_user: User = Depends(get_current_user), # 현재 로그인한 사용자 정보 주입
    x_organization_id: Optional[int] = Header(None, alias="X-Organization-ID") # HTTP 헤더에서 조직 ID 추출
) -> List[RoleResponse]:
    """
    현재 사용자의 컨텍스트에 따라 접근 가능한 역할 목록을 조회합니다.
    
    - **권한:** `role:read` 권한이 필요합니다.
    - **헤더:** `X-Organization-ID` 헤더를 통해 조직 컨텍스트를 지정할 수 있습니다.
    - **응답:** `RoleResponse` 스키마 목록을 반환합니다.
    """
    # 역할 조회 비즈니스 로직을 담당하는 프로바이더 호출
    roles = role_query_provider.get_accessible_roles(
        db,
        actor_user=current_user,
        organization_id=x_organization_id
    )
    return roles


# --- 역할 수정 API ---
@router.put(
    "/{role_id}",
    response_model=RoleResponse, # 성공 시 반환될 데이터 모델
    dependencies=[Depends(PermissionChecker("role:update"))] # 'role:update' 권한이 있는 사용자만 접근 가능
)
def update_role(
    db: Session = Depends(get_db), # 데이터베이스 세션 종속성 주입
    current_user: User = Depends(get_current_user), # 현재 로그인한 사용자 정보 주입
    role_id: int = Path(..., title="The ID of the role to update"), # 경로 파라미터에서 역할 ID 추출
    role_in: RoleUpdate = Body(...) # 요청 본문으로부터 RoleUpdate 스키마 데이터 파싱
) -> RoleResponse:
    """
    특정 역할을 수정합니다.
    
    - **권한:** `role:update` 권한이 필요합니다.
    - **경로 파라미터:** `role_id` (수정할 역할의 고유 ID).
    - **요청 본문:** `RoleUpdate` 스키마에 정의된 업데이트할 역할 정보를 포함해야 합니다.
    - **응답:** 수정된 역할의 `RoleResponse` 스키마 데이터를 반환합니다.
    - **예외:**
        - `NotFoundError` (404 Not Found): 지정된 `role_id`를 가진 역할을 찾을 수 없는 경우.
        - `DuplicateEntryError` (409 Conflict): 변경하려는 이름이 이미 존재하는 경우.
        - `HTTPException` (500 Internal Server Error): 예상치 못한 서버 오류 발생 시.
    """
    try:
        update_role_policy_provider.execute(db=db, actor_user=current_user, role_id=role_id, role_in=role_in)
        updated_role = role_command_provider.update_role(db, role_id=role_id, role_in=role_in, actor_user=current_user)
        db.commit() # 변경사항 데이터베이스에 커밋
        return updated_role
    except (NotFoundError, DuplicateEntryError) as e:
        db.rollback()
        # 404 또는 409 응답
        raise HTTPException(status_code=404 if isinstance(e, NotFoundError) else 409, detail=str(e))
    except ForbiddenError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


# --- 역할 삭제 API ---
@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT, # 성공 시 HTTP 204 상태 코드 반환 (본문 없음)
    dependencies=[Depends(PermissionChecker("role:delete"))] # 'role:delete' 권한이 있는 사용자만 접근 가능
)
def delete_role(
    db: Session = Depends(get_db), # 데이터베이스 세션 종속성 주입
    current_user: User = Depends(get_current_user), # 현재 로그인한 사용자 정보 주입
    role_id: int = Path(..., title="The ID of the role to delete") # 경로 파라미터에서 역할 ID 추출
):
    """
    특정 역할을 삭제합니다.
    
    - **권한:** `role:delete` 권한이 필요합니다.
    - **경로 파라미터:** `role_id` (삭제할 역할의 고유 ID).
    - **응답:** 성공 시 본문 없는 HTTP 204 응답을 반환합니다.
    - **예외:**
        - `NotFoundError` (404 Not Found): 지정된 `role_id`를 가진 역할을 찾을 수 없는 경우.
        - `HTTPException` (500 Internal Server Error): 예상치 못한 서버 오류 발생 시.
    """
    try:
        delete_role_policy_provider.execute(db, actor_user=current_user, role_id=role_id)

        role_command_provider.delete_role(db, role_id=role_id, actor_user=current_user)
        db.commit()
    except NotFoundError as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except (ForbiddenError, ConflictError) as e:
        db.rollback()
        raise HTTPException(status_code=403 if isinstance(e, ForbiddenError) else 409, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


# --- 역할에 할당된 권한 조회 API ---
@router.get(
    "/{role_id}/permissions",
    response_model=List[RolePermissionResponse], # 성공 시 반환될 데이터 모델 목록
    dependencies=[Depends(PermissionChecker("role:read"))] # 'role:read' 권한이 있는 사용자만 접근 가능
)
def get_role_permissions(
    db: Session = Depends(get_db), # 데이터베이스 세션 종속성 주입
    role_id: int = Path(..., title="The ID of the role to get permissions for") # 경로 파라미터에서 역할 ID 추출
) -> List[RolePermissionResponse]:
    """
    특정 역할에 할당된 모든 권한 및 ABAC 규칙의 목록을 조회합니다.
    
    - **권한:** `role:read` 권한이 필요합니다.
    - **경로 파라미터:** `role_id` (권한을 조회할 역할의 고유 ID).
    - **응답:** `RolePermissionResponse` 스키마 목록을 반환합니다.
    """
    # 역할 권한 조회 비즈니스 로직을 담당하는 프로바이더 호출
    permissions = role_query_provider.get_permissions_for_role(db, role_id=role_id)
    return permissions


# --- 역할 권한 업데이트 API (ABAC 규칙 포함) ---
@router.put(
    "/{role_id}/permissions",
    status_code=status.HTTP_204_NO_CONTENT, # 성공 시 HTTP 204 상태 코드 반환 (본문 없음)
    dependencies=[Depends(PermissionChecker("role:update"))] # 'role:update' 권한이 있는 사용자만 접근 가능
)
def update_role_permissions(
    db: Session = Depends(get_db), # 데이터베이스 세션 종속성 주입
    current_user: User = Depends(get_current_user), # 현재 로그인한 사용자 정보 주입
    role_id: int = Path(..., title="The ID of the role to update permissions for"), # 경로 파라미터에서 역할 ID 추출
    update_data: RolePermissionUpdateRequest = Body(...), # 요청 본문으로부터 RolePermissionUpdateRequest 스키마 데이터 파싱
    x_organization_id: Optional[int] = Header(None, alias="X-Organization-ID") # HTTP 헤더에서 조직 ID 추출
):
    """
    역할에 할당된 권한 목록을 업데이트합니다.
    이 작업은 전체 덮어쓰기(overwrite)로 동작하며, ABAC 규칙(허용된 컬럼, 필터 조건)을 포함할 수 있습니다.
    모든 비즈니스 규칙과 안전 장치는 정책(Policy) 계층에서 처리됩니다.
    
    - **권한:** `role:update` 권한이 필요합니다.
    - **경로 파라미터:** `role_id` (권한을 업데이트할 역할의 고유 ID).
    - **요청 본문:** `RolePermissionUpdateRequest` 스키마에 정의된 업데이트할 권한 목록을 포함해야 합니다.
    - **응답:** 성공 시 본문 없는 HTTP 204 응답을 반환합니다.
    - **예외:**
        - `NotFoundError` (404 Not Found): 지정된 `role_id`를 가진 역할을 찾을 수 없는 경우.
        - `PermissionDeniedError` (403 Forbidden): 정책(Policy)에 정의된 안전 장치 규칙(예: 상위 역할 수정 금지, 자신이 가지지 않은 권한 부여 시도 등) 위반 시.
        - `HTTPException` (500 Internal Server Error): 예상치 못한 서버 오류 발생 시.
    """
    try:
        # 정책 프로바이더를 통해 역할 권한 업데이트에 대한 모든 비즈니스 규칙 및 안전 장치 로직 실행
        update_role_permissions_policy_provider.execute(
            db, 
            actor_user=current_user, 
            target_role_id=role_id, 
            permissions_in=update_data.permissions,
            x_organization_id=x_organization_id
        )

        # 정책을 통과하면, 실제 DB 업데이트 비즈니스 로직을 담당하는 프로바이더 호출
        role_command_provider.update_permissions_for_role(
            db,
            role_id=role_id,
            permissions_in=update_data.permissions,
            actor_user=current_user
        )
        db.commit() # 변경사항 데이터베이스에 커밋
    except (NotFoundError, PermissionDeniedError) as e:
        db.rollback() # 오류 발생 시 트랜잭션 롤백
        # NotFoundError는 404, PermissionDeniedError는 403으로 명시적 처리
        raise HTTPException(status_code=403 if isinstance(e, PermissionDeniedError) else 404, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")