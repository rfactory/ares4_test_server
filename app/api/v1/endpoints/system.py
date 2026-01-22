from typing import List, Tuple, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Path, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, PermissionChecker
from app.models.objects.user import User
from app.domains.inter_domain.user_identity.schemas.user_identity_query import MemberResponse
from app.domains.inter_domain.user_identity.schemas.user_identity_command import RoleIdRequest
from app.domains.inter_domain.user_identity.user_identity_query_provider import user_identity_query_provider
from app.domains.inter_domain.policies.system_management.manage_system_member_policy_provider import manage_system_member_policy_provider

router = APIRouter()

@router.get("/members", response_model=List[MemberResponse])
async def read_system_members(
    db: Session = Depends(get_db),
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user),
    _permission: None = Depends(PermissionChecker(required_permission="system_members:read"))
):
    """
    시스템 컨텍스트의 구성원(스태프) 목록을 조회합니다.
    """
    current_user, _, _ = user_info
    members = user_identity_query_provider.get_members_by_system(db=db)
    return members

@router.put("/members/{user_id}", response_model=MemberResponse)
async def update_system_member_role(
    user_id: int = Path(..., title="The ID of the user to update"),
    role_update: RoleIdRequest = Body(...),
    db: Session = Depends(get_db),
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user)
):
    """
    시스템 구성원의 역할을 업데이트합니다.
    """
    current_user, _, _ = user_info
    updated_assignment = await manage_system_member_policy_provider.update_role(
        db=db, 
        actor_user=current_user, 
        target_user_id=user_id, 
        new_role_id=role_update.role_id
    )
    return MemberResponse(
        id=updated_assignment.user.id,
        username=updated_assignment.user.username,
        email=updated_assignment.user.email,
        role=updated_assignment.role.name
    )

@router.delete("/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_system_member(
    user_id: int = Path(..., title="The ID of the user to remove"),
    db: Session = Depends(get_db),
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user)
):
    """
    시스템 구성원의 역할을 제거합니다.
    """
    current_user, _, _ = user_info
    manage_system_member_policy_provider.remove(
        db=db, 
        actor_user=current_user, 
        user_to_remove_id=user_id
    )
    return