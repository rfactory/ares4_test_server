from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Path, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, PermissionChecker
from app.models.objects.user import User
from app.core.schemas.user import UserRolesUpdate, SwitchContextRequest
from app.core.exceptions import ForbiddenError, NotFoundError, ConflictError
# 정책 프로바이더 임포트
from app.domains.inter_domain.policies.user_management.update_user_roles_policy_provider import update_user_roles_policy_provider
from app.domains.inter_domain.policies.user_management.switch_context_policy_provider import switch_context_policy_provider

router = APIRouter()


@router.get("/me/contexts", 
    # response_model=ContextResponse # 스키마 정의 후 활성화
)
def get_my_contexts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Dict[str, List[Dict[str, Any]]]:
    """
    현재 로그인한 사용자가 접근 가능한 모든 컨텍스트의 목록을 조회합니다.
    - 개인, 시스템 관리, 그리고 소속된 모든 조직 및 해당 조직에서의 역할을 포함합니다.
    """
    contexts = []

    # 1. 개인 컨텍스트는 항상 추가
    contexts.append({
        "uniqueId": "personal", 
        "name": "Personal Space", 
        "type": "PERSONAL", 
        "organizationId": None, 
        "roleName": None
    })

    # 2. 사용자의 역할 할당을 통해 시스템 및 조직 컨텍스트 추가
    assignments = current_user.user_role_assignments
    
    for assignment in assignments:
        if assignment.role.scope == 'SYSTEM':
            contexts.append({
                "uniqueId": "system", 
                "name": "System", 
                "type": "SYSTEM", 
                "organizationId": None, 
                "roleName": assignment.role.name
            })
        elif assignment.role.scope == 'ORGANIZATION' and assignment.organization:
            contexts.append({
                "uniqueId": f"org-{assignment.organization.id}", 
                "name": f"{assignment.organization.company_name}", 
                "type": "ORGANIZATION", 
                "organizationId": assignment.organization.id, 
                "roleName": assignment.role.name
            })

    return {"contexts": contexts}


@router.post("/me/switch-context")
def switch_context(
    *, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: SwitchContextRequest,
):
    """시스템 관리자가 다른 조직의 컨텍스트로 전환합니다."""
    try:
        # To-Do: This should return a new JWT with temporary claims
        organization = switch_context_policy_provider.switch_to_organization_context(
            db,
            actor_user=current_user,
            target_organization_id=request.target_organization_id
        )
        return {"message": f"Successfully switched to context of organization {organization.company_name}"}
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.put("/users/{user_id}/roles", status_code=status.HTTP_204_NO_CONTENT)
def update_user_roles(
    *, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_id: int = Path(..., title="The ID of the user to update"),
    roles_in: UserRolesUpdate,
    _permission: None = Depends(PermissionChecker("user:update:role"))
):
    """
    사용자의 역할을 업데이트합니다 (할당 및 해제).
    이 엔드포인트는 복잡한 T0 거버넌스 규칙을 포함하는 정책을 실행합니다.
    """
    try:
        update_user_roles_policy_provider.execute(
            db=db,
            actor_user_id=current_user.id,
            target_user_id=user_id,
            role_ids_to_assign=roles_in.assign_role_ids,
            role_ids_to_revoke=roles_in.revoke_role_ids
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")
