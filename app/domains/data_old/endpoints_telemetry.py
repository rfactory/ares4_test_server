from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.dependencies import get_db, get_current_user
from app.domains.data.schemas import TelemetryDataCreate, TelemetryDataResponse
from app.domains.data.crud import telemetry_crud
from app.models.objects.user import User as DBUser
from app.core.exceptions import PermissionDeniedError, NotFoundError

router = APIRouter()

@router.post("/telemetry", response_model=TelemetryDataResponse, status_code=status.HTTP_201_CREATED)
def create_telemetry_data_endpoint(
    telemetry_data: TelemetryDataCreate, 
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    """
    Ingest new telemetry data. Authorization is checked inside the CRUD method.
    """
    try:
        db_telemetry = telemetry_crud.create_telemetry_data(
            db=db, telemetry_data=telemetry_data, request_user=current_user
        )
        return db_telemetry
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/telemetry/{telemetry_data_id}", response_model=TelemetryDataResponse)
def get_telemetry_data_endpoint(
    telemetry_data_id: int, 
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    """
    Retrieve a single telemetry data record by its ID. Authorization is checked inside the CRUD method.
    """
    try:
        db_telemetry = telemetry_crud.get_telemetry_data(
            db=db, telemetry_data_id=telemetry_data_id, request_user=current_user
        )
        return db_telemetry
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/telemetry", response_model=List[TelemetryDataResponse])
def get_multiple_telemetry_data_endpoint(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    device_id: Optional[int] = Query(None),
    metric_name: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None, description="Filter by timestamp greater than or equal to (ISO 8601 format)"),
    end_time: Optional[datetime] = Query(None, description="Filter by timestamp less than or equal to (ISO 8601 format)")
):
    """
    Retrieve multiple telemetry data records with optional filtering and pagination.
    Authorization is checked inside the CRUD method.
    """
    try:
        # Ensure timezone-aware datetimes for comparison if provided
        if start_time and start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        if end_time and end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)

        telemetry_data_list = telemetry_crud.get_multiple_telemetry_data(
            db=db,
            request_user=current_user,
            skip=skip,
            limit=limit,
            device_id=device_id,
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time
        )
        return telemetry_data_list
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
