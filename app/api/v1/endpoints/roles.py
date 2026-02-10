from typing import List, Optional, Tuple
from fastapi import APIRouter, Depends, Header, Path, HTTPException, status, Body, Query
from sqlalchemy.orm import Session

# 애플리케이션 핵심 종속성 및 예외
from app.dependencies import get_db, get_current_user, PermissionChecker
from app.core.exceptions import (
    PermissionDeniedError, NotFoundError, DuplicateEntryError, 
    ForbiddenError, ConflictError, AppLogicError
)

# 스키마 및 프로바이더
from app.domains.inter_domain.role_management.schemas.role_query import RoleResponse, RolePermissionResponse
from app.domains.inter_domain.role_management.schemas.role_command import RolePermissionUpdateRequest, RoleCreate, RoleUpdate
from app.domains.inter_domain.role_management.role_query_provider import role_query_provider

# 정책 프로바이더 (지휘관)
from app.domains.inter_domain.policies.role_management.update_role_permissions_policy_provider import update_role_permissions_policy_provider
from app.domains.inter_domain.policies.role_management.create_role_policy_provider import create_role_policy_provider
from app.domains.inter_domain.policies.role_management.delete_role_policy_provider import delete_role_policy_provider
from app.domains.inter_domain.policies.role_management.update_role_policy_provider import update_role_policy_provider
from app.domains.inter_domain.policies.role_management.get_assignable_roles_policy_provider import get_assignable_roles_policy_provider

from app.models.objects.user import User

router = APIRouter()

# --- 역할 조회 API (할당 가능 목록) ---
@router.get("/assignable", response_model=List[RoleResponse])
async def get_assignable_roles(
    db: Session = Depends(get_db),
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user),
    organization_id: Optional[int] = Query(None, description="organization context id to search assignable roles"),
    _permission: None = Depends(PermissionChecker("role:read"))
) -> List[RoleResponse]:
    """현재 사용자가 특정 컨텍스트에서 할당할 수 있는 역할 목록을 조회합니다."""
    current_user, _, _ = user_info
    # 조회의 경우 정책 지휘관이 권한 필터링 결과를 반환합니다.
    return get_assignable_roles_policy_provider.execute(
        db, actor_user=current_user, organization_id=organization_id
    )

# --- 역할 생성 API ---
@router.post(
    "",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionChecker("role:create"))]
)
async def create_role(
    db: Session = Depends(get_db),
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user),
    role_in: RoleCreate = Body(...),
    x_organization_id: Optional[int] = Header(None, alias="X-Organization-ID")
) -> RoleResponse:
    """
    새로운 역할을 생성합니다 (SYSTEM 또는 ORGANIZATION 스코프).
    Ares Aegis: 생성 로직, 감사 로그, 트랜잭션 커밋은 Policy 내부에서 완결됩니다.
    """
    current_user, _, _ = user_info
    try:
        # Policy 지휘관이 내부적으로 Command Service를 호출하고 최종 커밋까지 수행합니다.
        return create_role_policy_provider.execute(
            db, actor_user=current_user, role_in=role_in, x_organization_id=x_organization_id
        )
    except (DuplicateEntryError, ConflictError) as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (ForbiddenError, PermissionDeniedError) as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Role creation failed: {e}")

# --- 역할 목록 조회 API ---
@router.get(
    "",
    response_model=List[RoleResponse],
    dependencies=[Depends(PermissionChecker("role:read"))]
)
async def get_roles(
    db: Session = Depends(get_db),
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user),
    x_organization_id: Optional[int] = Header(None, alias="X-Organization-ID")
) -> List[RoleResponse]:
    """현재 컨텍스트에서 접근 가능한 역할 목록을 조회합니다. (조회형)"""
    current_user, _, _ = user_info
    return role_query_provider.get_accessible_roles(
        db, actor_user=current_user, organization_id=x_organization_id
    )

# --- 역할 수정 API ---
@router.put(
    "/{role_id}",
    response_model=RoleResponse,
    dependencies=[Depends(PermissionChecker("role:update"))]
)
async def update_role(
    db: Session = Depends(get_db),
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user),
    role_id: int = Path(..., title="role id to update"),
    role_in: RoleUpdate = Body(...)
) -> RoleResponse:
    """역할 정보를 수정합니다."""
    current_user, _, _ = user_info
    try:
        # Policy 내부에서 완결성 보장
        return update_role_policy_provider.execute(
            db=db, actor_user=current_user, role_id=role_id, role_in=role_in
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (DuplicateEntryError, ConflictError) as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Update failed: {e}")

# --- 역할 삭제 API ---
@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(PermissionChecker("role:delete"))]
)
async def delete_role(
    db: Session = Depends(get_db),
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user),
    role_id: int = Path(..., title="role id to delete")
):
    """역할을 삭제합니다."""
    current_user, _, _ = user_info
    try:
        delete_role_policy_provider.execute(db, actor_user=current_user, role_id=role_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ForbiddenError, ConflictError) as e:
        raise HTTPException(status_code=403 if isinstance(e, ForbiddenError) else 409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Delete failed: {e}")

# --- 역할 권한 조회 및 업데이트 API ---
@router.get("/{role_id}/permissions", response_model=List[RolePermissionResponse])
async def get_role_permissions(
    db: Session = Depends(get_db),
    role_id: int = Path(..., title="search permissions for this role ID"),
    _permission: None = Depends(PermissionChecker("role:read"))
) -> List[RolePermissionResponse]:
    """특정 역할에 부여된 권한 목록을 조회합니다."""
    return role_query_provider.get_permissions_for_role(db, role_id=role_id)

@router.put("/{role_id}/permissions", status_code=status.HTTP_204_NO_CONTENT)
async def update_role_permissions(
    db: Session = Depends(get_db),
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user),
    role_id: int = Path(..., title="Update permissions for this role ID"),
    update_data: RolePermissionUpdateRequest = Body(...),
    x_organization_id: Optional[int] = Header(None, alias="X-Organization-ID")
):
    """역할의 권한 구성을 변경합니다."""
    current_user, _, _ = user_info
    try:
        # Policy가 비즈니스 검증, 권한 매핑, 감사 로그 기록 및 커밋을 일괄 처리합니다.
        update_role_permissions_policy_provider.execute(
            db, actor_user=current_user, target_role_id=role_id, 
            permissions_in=update_data.permissions, x_organization_id=x_organization_id
        )
    except (NotFoundError, PermissionDeniedError, AppLogicError) as e:
        raise HTTPException(status_code=403 if isinstance(e, PermissionDeniedError) else 404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Permissions update failed: {e}")