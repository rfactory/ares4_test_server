from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.domains.devices.schemas import Device, DeviceCreate, DeviceUpdate
from app.domains.devices.crud import device_crud
from app.core.security import get_current_user
from app.models.objects.user import User as DBUser # 현재 사용자 정보 가져오기 위함

router = APIRouter()

@router.post("/", response_model=Device, status_code=status.HTTP_201_CREATED, summary="Create a new device")
def create_device(
    device: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user) # 인증된 사용자만 접근 가능
):
    # TODO: RBAC (Role-Based Access Control) 로직 추가
    # 예: current_user가 장치를 생성할 권한이 있는지 확인
    
    # CPU Serial 중복 확인
    db_device = device_crud.get_by_cpu_serial(db, cpu_serial=device.cpu_serial)
    if db_device:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Device with this CPU serial already exists")
    
    # UUID 중복 확인
    db_device = device_crud.get_by_current_uuid(db, current_uuid=device.current_uuid)
    if db_device:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Device with this UUID already exists")

    return device_crud.create(db=db, obj_in=device)

@router.get("/", response_model=List[Device], summary="Retrieve multiple devices")
def read_devices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user) # 인증된 사용자만 접근 가능
):
    # TODO: RBAC 로직 추가
    # 예: current_user가 접근할 수 있는 장치만 반환
    devices = device_crud.get_multi(db, skip=skip, limit=limit)
    return devices

@router.get("/{device_id}", response_model=Device, summary="Retrieve a single device by ID")
def read_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user) # 인증된 사용자만 접근 가능
):
    # TODO: RBAC 로직 추가
    # 예: current_user가 해당 device_id에 접근할 권한이 있는지 확인
    db_device = device_crud.get(db, id=device_id)
    if db_device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return db_device

@router.put("/{device_id}", response_model=Device, summary="Update an existing device by ID")
def update_device(
    device_id: int,
    device: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user) # 인증된 사용자만 접근 가능
):
    # TODO: RBAC 로직 추가
    # 예: current_user가 해당 device_id를 업데이트할 권한이 있는지 확인
    db_device = device_crud.get(db, id=device_id)
    if db_device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    
    return device_crud.update(db=db, db_obj=db_device, obj_in=device)

@router.delete("/{device_id}", response_model=Device, summary="Delete a device by ID")
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user) # 인증된 사용자만 접근 가능
):
    # TODO: RBAC 로직 추가
    # 예: current_user가 해당 device_id를 삭제할 권한이 있는지 확인
    db_device = device_crud.get(db, id=device_id)
    if db_device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    
    device_crud.delete(db=db, id=device_id)
    return db_device
