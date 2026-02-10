from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import uuid

from app.core.exceptions import AppLogicError

from ..crud.device_query_crud import device_query_crud
from ..schemas.device_query import DeviceQuery, DeviceRead

class DeviceManagementQueryService:
    def get_devices(self, db: Session, *, query_params: DeviceQuery) -> List[DeviceRead]:
        """DeviceQuery 스키마를 사용하여 장치 목록을 동적으로 조회합니다."""
        db_devices = device_query_crud.get_multi(db, query_params=query_params)
        return [DeviceRead.model_validate(device) for device in db_devices]

    def get_device_by_id(self, db: Session, *, id: int) -> Optional[DeviceRead]:
        """ID로 단일 장치를 조회합니다."""
        db_device = device_query_crud.get(db, id=id)
        return DeviceRead.model_validate(db_device) if db_device else None

    def get_device_by_uuid(self, db: Session, *, current_uuid: UUID) -> Optional[DeviceRead]:
        """UUID로 단일 장치를 조회합니다."""
        query_params = DeviceQuery(current_uuid=current_uuid)
        db_devices = device_query_crud.get_multi(db, query_params=query_params)
        return DeviceRead.model_validate(db_devices[0]) if db_devices else None

    # --- ACL 검증을 위한 핵심 중계 메서드 ---
    def get_device_by_identifier(self, db: Session, *, identifier: str) -> Optional[DeviceRead]:
        """
        UUID 또는 CPU Serial을 통해 장치를 조회하고 스키마로 변환합니다.
        CRUD 레이어에서 이미 joinedload가 적용되어 있으므로 소유권 정보가 포함됩니다.
        """
        is_valid_uuid = False
        try:
            # 하이픈 유무와 상관없이 UUID 형식인지 체크
            uuid.UUID(identifier)
            is_valid_uuid = True
        except (ValueError, AttributeError):
            is_valid_uuid = False

        if is_valid_uuid:
            # 1. UUID 형식이면 UUID로 조회 시도
            # (만약 여기서 못 찾으면 시리얼로 한 번 더 찾는 로직을 넣을 수도 있습니다)
            db_device = device_query_crud.get_by_uuid(db, current_uuid=identifier)
            if not db_device:
                db_device = device_query_crud.get_by_serial(db, serial=identifier)
        else:
            # 2. UUID 형식이 아니면 안전하게 시리얼로만 조회
            db_device = device_query_crud.get_by_serial(db, serial=identifier)

        if not db_device:
            return None
            
        return DeviceRead.model_validate(db_device)
    
    def get_by_serial(self, db: Session, *, serial: str) -> Optional[DeviceRead]:
        """시리얼 번호로 장치를 조회합니다. (Factory Enrollment Policy용)"""
        return self.get_device_by_identifier(db, identifier=serial)
    
    def ensure_device_is_enrollee(self, db: Session, serial: str):
        """
        기기가 신규 등록 가능한 상태인지 확인합니다.
        이미 등록된 기기일 경우 AppLogicError를 발생시켜 흐름을 중단합니다.
        """
        existing_device = self.get_by_serial(db, serial=serial)
        if existing_device:
            # Policy가 직접 판단하던 "중복 등록 방지" 로직을 쿼리 서비스가 담당합니다.
            raise AppLogicError(f"Device with serial {serial} is already enrolled.")

device_management_query_service = DeviceManagementQueryService()