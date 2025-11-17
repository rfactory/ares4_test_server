from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.dependencies import get_db
from app.domains.data.schemas import TelemetryDataCreate, TelemetryDataResponse, TelemetryDataUpdate
from app.domains.data.crud import telemetry_crud

router = APIRouter()

@router.post("/telemetry", response_model=TelemetryDataResponse, status_code=status.HTTP_201_CREATED)
def create_telemetry_data_endpoint(
    telemetry_data: TelemetryDataCreate, db: Session = Depends(get_db)
):
    """
    Ingest new telemetry data from a device.
    """
    db_telemetry = telemetry_crud.create_telemetry_data(db=db, telemetry_data=telemetry_data)
    return db_telemetry

@router.get("/telemetry/{telemetry_data_id}", response_model=TelemetryDataResponse)
def get_telemetry_data_endpoint(telemetry_data_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single telemetry data record by its ID.
    """
    db_telemetry = telemetry_crud.get_telemetry_data(db=db, telemetry_data_id=telemetry_data_id)
    if db_telemetry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telemetry data not found")
    return db_telemetry

@router.get("/telemetry", response_model=List[TelemetryDataResponse])
def get_multiple_telemetry_data_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    device_id: Optional[int] = Query(None),
    metric_name: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None, description="Filter by timestamp greater than or equal to (ISO 8601 format)"),
    end_time: Optional[datetime] = Query(None, description="Filter by timestamp less than or equal to (ISO 8601 format)"),
    db: Session = Depends(get_db)
):
    """
    Retrieve multiple telemetry data records with optional filtering and pagination.
    """
    # Ensure timezone-aware datetimes for comparison if provided
    if start_time and start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time and end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)

    telemetry_data_list = telemetry_crud.get_multiple_telemetry_data(
        db=db,
        skip=skip,
        limit=limit,
        device_id=device_id,
        metric_name=metric_name,
        start_time=start_time,
        end_time=end_time
    )
    return telemetry_data_list

@router.patch("/telemetry/{telemetry_data_id}", response_model=TelemetryDataResponse)
def update_telemetry_data_endpoint(
    telemetry_data_id: int,
    telemetry_data_update: TelemetryDataUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing telemetry data record.
    """
    db_telemetry = telemetry_crud.update_telemetry_data(
        db=db, telemetry_data_id=telemetry_data_id, telemetry_data_update=telemetry_data_update
    )
    if db_telemetry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telemetry data not found")
    return db_telemetry

@router.delete("/telemetry/{telemetry_data_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_telemetry_data_endpoint(telemetry_data_id: int, db: Session = Depends(get_db)):
    """
    Delete a telemetry data record by its ID.
    """
    db_telemetry = telemetry_crud.delete_telemetry_data(db=db, telemetry_data_id=telemetry_data_id)
    if db_telemetry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telemetry data not found")
    return None
