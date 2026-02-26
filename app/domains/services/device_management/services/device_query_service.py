from sqlalchemy.orm import Session, undefer
from typing import List, Optional
from uuid import UUID
import uuid

from app.core.exceptions import AppLogicError
from app.models.objects.device import Device as DBDevice

from ..crud.device_query_crud import device_query_crud
from ..schemas.device_query import DeviceQuery, DeviceRead

class DeviceManagementQueryService:
    def __init__(self):
        # [수정] 전역으로 존재하는 crud를 인스턴스 속성으로 등록해야 
        # 정책(Policy)에서 .device_query_crud 로 접근이 가능합니다.
        from ..crud.device_query_crud import device_query_crud
        self.device_query_crud = device_query_crud
        
    def get_devices(self, db: Session, *, query_params: DeviceQuery) -> List[DeviceRead]:
        """DeviceQuery 스키마를 사용하여 장치 목록을 동적으로 조회합니다."""
        db_devices = device_query_crud.get_multi(db, query_params=query_params)
        return [DeviceRead.model_validate(device) for device in db_devices]

    def get_device_by_id(self, db: Session, *, id: int) -> Optional[DeviceRead]:
        """ID로 단일 장치를 조회합니다."""
        db_device = device_query_crud.get(db, id=id)
        return DeviceRead.model_validate(db_device) if db_device else None

    def get_device_by_uuid(self, db: Session, *, current_uuid: UUID) -> Optional[DeviceRead]:
        """UUID로 단일 장치를 조회하여 DeviceRead 스키마로 반환합니다."""
        db_device = self.get_device_model_by_uuid(db, current_uuid=current_uuid)
        return DeviceRead.model_validate(db_device) if db_device else None
    
    def get_device_model_by_uuid(self, db: Session, *, current_uuid: UUID) -> Optional[DBDevice]:
        """
        [내부용] Pydantic 변환 없이 SQLAlchemy 모델 원본을 반환합니다.
        hmac_secret_key와 같이 deferred된 민감 필드를 강제로 로드합니다.
        """
        # 1. 기존 유저님의 방식인 DeviceQuery를 사용하면서도
        # 2. hmac_secret_key를 undefer로 끄집어냅니다.
        query_params = DeviceQuery(current_uuid=current_uuid)
        
        # CRUD의 get_multi를 쓰되, 쿼리 옵션에 undefer를 적용하기 위해 직접 쿼리하거나 
        # CRUD에 옵션을 넘기는 방식이 좋지만, 가장 확실한 방법은 아래와 같습니다.
        db_device = db.query(DBDevice).options(
            undefer(DBDevice.hmac_secret_key)
        ).filter(
            DBDevice.current_uuid == str(current_uuid)
        ).first()
        
        return db_device

    # --- ACL 검증을 위한 핵심 중계 메서드 ---
    def get_device_by_identifier(self, db: Session, *, identifier: str) -> Optional[DeviceRead]:
        """UUID 또는 CPU Serial을 통해 장치를 조회하고 스키마로 변환합니다."""
        is_valid_uuid = False
        try:
            uuid.UUID(identifier)
            is_valid_uuid = True
        except (ValueError, AttributeError):
            is_valid_uuid = False

        if is_valid_uuid:
            db_device = device_query_crud.get_by_uuid(db, current_uuid=identifier)
            if not db_device:
                db_device = device_query_crud.get_by_serial(db, serial=identifier)
        else:
            db_device = device_query_crud.get_by_serial(db, serial=identifier)

        if not db_device:
            return None
            
        return DeviceRead.model_validate(db_device)
    
    def get_by_serial(self, db: Session, *, serial: str) -> Optional[DeviceRead]:
        """시리얼 번호로 장치를 조회합니다."""
        return self.get_device_by_identifier(db, identifier=serial)
    
    def ensure_device_is_enrollee(self, db: Session, serial: str):
        """기기가 신규 등록 가능한 상태인지 확인합니다."""
        existing_device = self.get_by_serial(db, serial=serial)
        if existing_device:
            raise AppLogicError(f"Device with serial {serial} is already enrolled.")
        
    def get_count_by_unit(self, db: Session, *, unit_id: int) -> int:
        """해당 유닛에 현재 연결된 기기 숫자를 카운트합니다."""
        return db.query(DBDevice).filter(DBDevice.system_unit_id == unit_id).count()
    
    def has_master_device(self, db: Session, *, unit_id: int) -> bool:
        """해당 유닛에 이미 MASTER(LEADER) 기기가 존재하는지 확인합니다."""
        # Device 모델의 cluster_role 필드를 사용하여 확인합니다.
        from app.models.objects.device import ClusterRoleEnum
        master_exists = db.query(DBDevice).filter(
            DBDevice.system_unit_id == unit_id,
            DBDevice.cluster_role == ClusterRoleEnum.LEADER
        ).first()
        return master_exists is not None
device_management_query_service = DeviceManagementQueryService()