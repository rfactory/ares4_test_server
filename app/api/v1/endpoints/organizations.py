from typing import List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, PermissionChecker
from app.models.objects.user import User
from app.domains.inter_domain.organizations.schemas.organization_command import OrganizationCreate
from app.domains.inter_domain.organizations.schemas.organization_query import OrganizationResponse
from app.domains.inter_domain.user_identity.schemas.user_identity_query import MemberResponse
from app.domains.inter_domain.policies.organization_management.create_organization_policy_provider import create_organization_policy_provider
from app.domains.inter_domain.policies.organization_management.manage_organization_member_policy_provider import manage_organization_member_policy_provider
from app.domains.inter_domain.organizations.organization_query_provider import organization_query_provider
from app.domains.inter_domain.user_identity.user_identity_query_provider import user_identity_query_provider
from app.core.exceptions import PermissionDeniedError, DuplicateEntryError, NotFoundError, AppLogicError, ForbiddenError

router = APIRouter()

class UpdateMemberRoleRequest(BaseModel):
    new_role_id: int

@router.get("", response_model=List[OrganizationResponse])
async def get_organizations(
    db: Session = Depends(get_db),
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    _permission: None = Depends(PermissionChecker("organizations:read"))
):
    """
    조직 목록을 조회합니다.
    """
    current_user, _, _ = user_info
    orgs = organization_query_provider.get_organizations(
        db, skip=skip, limit=limit
    )
    return orgs

@router.get("/search", response_model=List[OrganizationResponse])
async def search_organizations(
    db: Session = Depends(get_db),
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user),
    search_term: str = Query(..., min_length=1),
    _permission: None = Depends(PermissionChecker("organizations:read")) # 모든 스태프가 조직을 검색할 수 있도록 함
):
    """
    조직 이름 또는 사업자 등록 번호로 조직을 검색합니다.
    """
    current_user, _, _ = user_info
    organizations = organization_query_provider.search_organizations(db, search_term=search_term)
    return organizations

@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: int = Path(..., description="The ID of the organization to retrieve"),
    db: Session = Depends(get_db),
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user),
    _permission: None = Depends(PermissionChecker("organizations:read"))
):
    """
    ID로 특정 조직의 상세 정보를 조회합니다.
    """
    current_user, _, _ = user_info
    org = organization_query_provider.get_organization_by_id(db, org_id=organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@router.post("", response_model=OrganizationResponse)
async def create_organization(
    *, 
    db: Session = Depends(get_db),
    org_in: OrganizationCreate,
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user),
    _permission: None = Depends(PermissionChecker("organization:create"))
):
    """
    새로운 조직을 생성합니다.
    """
    current_user, _, _ = user_info
    try:
        new_org = create_organization_policy_provider.execute(
            db, org_in=org_in, actor_user=current_user
        )
        db.commit()
        db.refresh(new_org)
        return new_org
    except PermissionDeniedError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(e))
    except DuplicateEntryError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))
    except NotFoundError as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@router.get("/{organization_id}/members", response_model=List[MemberResponse])
async def read_organization_members(
    organization_id: int = Path(..., description="The ID of the organization to retrieve members from"),
    db: Session = Depends(get_db),
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user),
    _permission: None = Depends(PermissionChecker(required_permission="organization_members:read"))
):
    """
    특정 조직의 구성원 목록을 조회합니다.
    """
    current_user, _, _ = user_info
    members = user_identity_query_provider.get_members_by_organization(db=db, organization_id=organization_id)
    if not members:
        raise HTTPException(status_code=404, detail="No members found for this organization or organization not found")
    return members

@router.delete("/{organization_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_organization_member(
    organization_id: int = Path(..., description="The ID of the organization"),
    user_id: int = Path(..., description="The ID of the user to remove"),
    db: Session = Depends(get_db),
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user)
):
    """조직에서 구성원을 제거합니다."""
    current_user, _, _ = user_info
    try:
        manage_organization_member_policy_provider.remove(
            db, actor_user=current_user, organization_id=organization_id, user_to_remove_id=user_id
        )
    except (PermissionDeniedError, ForbiddenError) as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NotFoundError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

@router.put("/{organization_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_organization_member_role(
    organization_id: int = Path(..., description="The ID of the organization"),
    user_id: int = Path(..., description="The ID of the user to update"),
    request: UpdateMemberRoleRequest = Body(...),
    db: Session = Depends(get_db),
    user_info: Tuple[User, str, Optional[str]] = Depends(get_current_user)
):
    """조직 구성원의 역할을 변경합니다."""
    current_user, _, _ = user_info
    try:
        manage_organization_member_policy_provider.update_role(
            db, actor_user=current_user, organization_id=organization_id, user_to_update_id=user_id, new_role_id=request.new_role_id
        )
    except (PermissionDeniedError, ForbiddenError) as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except (NotFoundError, AppLogicError) as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")