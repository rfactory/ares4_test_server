from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Optional, List
from uuid import UUID
import uuid  # [추가] UUID 형식 검증을 위해 반드시 필요합니다.

from app.models.objects.device import Device
from ..schemas.device_query import DeviceQuery

class CRUDDeviceQuery:
    def _get_base_query(self, db: Session):
        """관계 데이터를 미리 로드하는 공통 기본 쿼리입니다."""
        return db.query(Device).options(
            joinedload(Device.owner_organization), 
            joinedload(Device.owner_user)
        ).filter(Device.is_active == True)

    def get(self, db: Session, *, id: int) -> Optional[Device]:
        """ID로 장치를 조회하며 소유권 관계를 미리 로드합니다."""
        return self._get_base_query(db).filter(Device.id == id).first()

    def get_by_uuid(self, db: Session, *, current_uuid: str) -> Optional[Device]:
        """UUID로 장치를 안전하게 조회합니다."""
        try:
            # 문자열이 유효한 UUID 형식인지 검증하여 Postgres 에러 방지
            val = uuid.UUID(str(current_uuid))
            return self._get_base_query(db).filter(Device.current_uuid == val).first()
        except (ValueError, AttributeError):
            return None

    def get_by_serial(self, db: Session, *, serial: str) -> Optional[Device]:
        """CPU 시리얼로 장치를 조회합니다."""
        return self._get_base_query(db).filter(Device.cpu_serial == serial).first()

    def get_by_identifier(self, db: Session, *, identifier: str) -> Optional[Device]:
        """
        UUID 또는 CPU Serial을 통해 장치를 조회합니다. 
        Postgres의 UUID 타입 캐스팅 에러(InvalidTextRepresentation)를 방지하기 위해 
        입력값이 UUID 형식일 때만 current_uuid 컬럼을 대조합니다.
        """
        is_valid_uuid = False
        try:
            uuid.UUID(str(identifier))
            is_valid_uuid = True
        except (ValueError, AttributeError):
            is_valid_uuid = False

        query = self._get_base_query(db)

        if is_valid_uuid:
            # UUID 형식인 경우: 두 컬럼 모두 검색 (OR 조건)
            return query.filter(
                (Device.current_uuid == identifier) | (Device.cpu_serial == identifier)
            ).first()
        else:
            # UUID 형식이 아닌 경우: cpu_serial 컬럼만 검색 (에러 원천 차단)
            return query.filter(Device.cpu_serial == identifier).first()

    def get_multi(self, db: Session, *, query_params: DeviceQuery) -> List[Device]:
        """
        DeviceQuery 스키마 기반 동적 조회 시에도 관계 데이터를 포함합니다.
        제공해주신 모든 필터 로직이 포함되어 있습니다.
        """
        query = self._get_base_query(db)

        # 동적 필터링
        if query_params.id is not None:
            query = query.filter(Device.id == query_params.id)
        if query_params.cpu_serial:
            query = query.filter(Device.cpu_serial == query_params.cpu_serial)
        if query_params.current_uuid:
            # current_uuid 필터 시에도 안전을 위해 형식을 체크할 수 있습니다.
            query = query.filter(Device.current_uuid == query_params.current_uuid)
        if query_params.hardware_blueprint_id:
            query = query.filter(Device.hardware_blueprint_id == query_params.hardware_blueprint_id)
        if query_params.visibility_status:
            query = query.filter(Device.visibility_status == query_params.visibility_status)
        if query_params.status:
            query = query.filter(Device.status == query_params.status)
        if query_params.is_active is not None:
            query = query.filter(Device.is_active == query_params.is_active)

        # 정렬: 최신순
        query = query.order_by(Device.created_at.desc())

        return query.offset(query_params.skip).limit(query_params.limit).all()

device_query_crud = CRUDDeviceQuery()