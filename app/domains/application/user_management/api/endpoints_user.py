from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.dependencies import get_db, get_current_user
from app.models.objects.user import User as DBUser
from app.core.exceptions import DuplicateEntryError, NotFoundError

from app.domains.application.user_management.services.user_management_coordinator import user_management_coordinator
from app.domains.services.access_requests.schemas.access_request import AccessRequestCreate, AccessRequestUpdate, AccessRequestResponse

router = APIRouter()

# High-level API to create a user and initiate an access request (e.g., for enterprise users)
@router.post("/access-request", response_model=AccessRequestResponse, status_code=status.HTTP_201_CREATED, summary="Create user and initiate access request (orchestrated)")
async def create_user_and_request_access_api(
    access_request_in: AccessRequestCreate,
    db: Session = Depends(get_db),
    current_user: Optional[DBUser] = Depends(get_current_user) # Can be None for public registration
):
    try:
        return await user_management_coordinator.create_user_and_request_access(
            db=db,
            access_request_in=access_request_in,
        )
    except (DuplicateEntryError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# High-level API to retrieve access requests (orchestrated)
@router.get("/access-requests", response_model=List[AccessRequestResponse], summary="Retrieve access requests (orchestrated)")
async def get_all_access_requests_api(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user),
    status: Optional[str] = Query("pending", description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    return await user_management_coordinator.get_access_requests(db, current_user=current_user, status=status, skip=skip, limit=limit)


# High-level API to process an access request (orchestrated)
@router.put("/access-requests/{request_id}", response_model=AccessRequestResponse, summary="Process an access request (orchestrated)")
async def process_access_request_api(
    request_id: int,
    update_in: AccessRequestUpdate,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    return await user_management_coordinator.process_access_request_workflow(
        db=db,
        request_id=request_id,
        update_in=update_in,
        admin_user=current_user
    )
