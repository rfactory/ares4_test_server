from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, PermissionChecker
from app.models.objects.user import User
from app.domains.inter_domain.organizations.organization_query_provider import organization_query_provider
from app.domains.inter_domain.organizations.organization_command_provider import organization_command_provider
# Import schemas via inter_domain layer
from app.domains.inter_domain.organizations.schemas.organization_query import OrganizationTypeResponse
from app.domains.inter_domain.organizations.schemas.organization_command import OrganizationTypeCreate
from app.core.exceptions import DuplicateEntryError

router = APIRouter()

@router.get("", response_model=List[OrganizationTypeResponse])
def get_organization_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    """
    모든 조직 유형의 목록을 조회합니다.
    """
    org_types = organization_query_provider.get_organization_types(db, skip=skip, limit=limit)
    return org_types

@router.post("", response_model=OrganizationTypeResponse)
def create_organization_type(
    *,
    db: Session = Depends(get_db),
    org_type_in: OrganizationTypeCreate,
    current_user: User = Depends(get_current_user),
    _permission: None = Depends(PermissionChecker("organization_type:create")) # Assumes this permission will be created
):
    """
    새로운 조직 유형을 생성합니다.
    """
    try:
        # A validator to check for name uniqueness could be added here in a policy.
        new_org_type = organization_command_provider.create_organization_type(db, org_type_in=org_type_in)
        db.commit()
        db.refresh(new_org_type)
        return new_org_type
    except DuplicateEntryError as e: # Assuming the DB layer will raise this
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))
