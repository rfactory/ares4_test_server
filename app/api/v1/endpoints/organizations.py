from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, PermissionChecker
from app.models.objects.user import User
from app.domains.inter_domain.organizations.schemas.organization_command import OrganizationCreate
from app.domains.inter_domain.organizations.schemas.organization_query import OrganizationResponse
from app.domains.inter_domain.policies.organization_management.create_organization_policy_provider import create_organization_policy_provider
from app.domains.inter_domain.organizations.organization_query_provider import organization_query_provider
from app.core.exceptions import PermissionDeniedError, DuplicateEntryError, NotFoundError

router = APIRouter()

@router.get("/", response_model=List[OrganizationResponse])
def get_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    _permission: None = Depends(PermissionChecker("organizations:read"))
):
    """
    조직 목록을 조회합니다.
    """
    orgs = organization_query_provider.get_organizations(
        db, skip=skip, limit=limit
    )
    return orgs

@router.get("/search", response_model=List[OrganizationResponse])
def search_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search_term: str = Query(..., min_length=1),
    _permission: None = Depends(PermissionChecker("organizations:read")) # 모든 스태프가 조직을 검색할 수 있도록 함
):
    """
    조직 이름 또는 사업자 등록 번호로 조직을 검색합니다.
    """
    organizations = organization_query_provider.search_organizations(db, search_term=search_term)
    return organizations

@router.post("/", response_model=OrganizationResponse)
def create_organization(
    *, 
    db: Session = Depends(get_db),
    org_in: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    _permission: None = Depends(PermissionChecker("organization:create"))
):
    """
    새로운 조직을 생성합니다.
    """
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