import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import Tuple, Optional, Dict, Any, Union, List
from uuid import UUID

# --- Providers ---
from app.domains.inter_domain.device_management.device_internal_query_provider import device_internal_query_provider
from app.domains.inter_domain.supported_component_management.supported_component_query_provider import supported_component_query_provider
from app.domains.inter_domain.observation.observation_snapshot_command_provider import observation_snapshot_command_provider

# --- Validator Providers ---
from app.domains.inter_domain.validators.device_existence.provider import device_existence_validator_provider
from app.domains.inter_domain.validators.system_support.provider import system_support_validator_provider
from app.domains.inter_domain.validators.cpu_serial.provider import cpu_serial_validator_provider
from app.domains.inter_domain.validators.hmac_integrity.provider import hmac_integrity_validator_provider
from app.domains.inter_domain.validators.device_attachment.provider import device_attachment_validator_provider

# --- Command Providers ---
from app.domains.inter_domain.telemetry.telemetry_command_provider import telemetry_command_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
from app.domains.inter_domain.cache.sequence_cache_command_service_provider import sequence_cache_command_provider

# --- Schemas ---
from app.domains.inter_domain.telemetry.schemas.telemetry_command import TelemetryCommandDataCreate

# --- Models ---
from app.models.objects.user import User

logger = logging.getLogger(__name__)

class TelemetryIngestionPolicy:
    """
    텔레메트리 수신에 대한 전체 유효성 검사 및 처리 정책을 시행하는 '뇌(Brain)' 역할을 합니다.
    """
    def ingest(
        self, 
        db: Session, 
        *, 
        device_uuid_str: str, 
        topic: str, 
        payload: Dict[str, Any], 
        actor_user: Optional[User] = None
    ) -> Tuple[bool, Optional[str]]:
        try:
            # 0단계: 토픽 기본 검증
            if "telemetry" not in topic.lower():
                return False, "Topic mismatch"

            # 1단계: 핵심 정보(Device) 조회
            device = device_internal_query_provider.get_device_with_secret_by_uuid(
                db, 
                current_uuid=UUID(device_uuid_str)
            )

            # 2단계: 기기 존재 및 상태 검증
            is_valid, error_msg = device_existence_validator_provider.validate_device_existence(
                device=device
            )
            
            if not is_valid:
                self._log_audit_failure(db, "DEVICE_NOT_FOUND", error_msg, {"device_uuid": device_uuid_str})
                return False, error_msg

            # 3단계: 컴포넌트 타입 확인 및 시스템 지원 검증
            component_type = payload.get("component_type")
            supported_component = supported_component_query_provider.get_by_component_type(
                db, 
                component_type=component_type
            )
            
            is_valid, error_msg = system_support_validator_provider.validate(
                supported_component=supported_component
            )
            
            if not is_valid:
                return False, error_msg

            # 4단계: 보안 및 무결성 검증 (CPU, HMAC)
            # [알림] 여기서 호출하는 hmac_integrity_validator_provider는 우리가 고친 DB 기반 로직을 사용합니다.
            is_valid, error_msg = cpu_serial_validator_provider.validate(device=device, payload=payload)
            if not is_valid: return False, error_msg
            
            is_valid, error_msg = hmac_integrity_validator_provider.validate(db=db, device=device, payload=payload)
            if not is_valid: return False, error_msg

            # 5단계: 컨텍스트 검증 (Attachment, Blueprint)
            instance_name = payload.get("instance_name")
            is_valid, error_msg = device_attachment_validator_provider.validate(
                db=db, 
                device_id=device.id, 
                supported_component_id=supported_component.id, 
                instance_name=instance_name
            )
            if not is_valid: return False, error_msg

            # 6단계: 스냅샷 확보 (Observation Header)
            snapshot_id = payload.get("snapshot_id")
            snapshot = observation_snapshot_command_provider.get_or_create_snapshot(
                db=db, 
                snapshot_id=snapshot_id, 
                system_unit_id=device.id,
                observation_type="SENSOR"
            )
            
            # --- 6-1단계: 시퀀스 무결성 대조 ---
            current_full_seq = payload.get("sequence_number")
            if current_full_seq is not None:
                self._reconcile_sequence(db, device.id, instance_name, current_full_seq)
            
            # 7단계: 데이터 저장 (Telemetry Data)
            data_to_save: List[Dict[str, Any]] = payload.get('data', [])
            telemetry_create_list = []

            for reading in data_to_save:
                captured_at = self._parse_timestamp(reading.get('timestamp'))
                avg_val = reading.get('avg_value')
                if avg_val is None:
                    avg_val = reading.get('avg', reading.get('value'))
                
                telemetry_create_list.append(
                    TelemetryCommandDataCreate(
                        device_id=device.id, 
                        system_unit_id=device.system_unit_id, 
                        snapshot_id=snapshot.id, 
                        component_name=instance_name,  # 스키마에 추가한 필드에 instance_name 주입
                        metric_name=reading.get('metric_name'),
                        unit=supported_component.unit, 
                        avg_value=avg_val, 
                        min_value=reading.get('min_value') if reading.get('min_value') is not None else reading.get('min', avg_val),
                        max_value=reading.get('max_value') if reading.get('max_value') is not None else reading.get('max', avg_val),
                        std_dev=reading.get('std_dev') if reading.get('std_dev') is not None else 0.0,
                        slope=reading.get('slope') if reading.get('slope') is not None else 0.0,
                        sample_count=reading.get('sample_count') if reading.get('sample_count') is not None else reading.get('count', 1),
                        captured_at=captured_at,
                        extra_stats=reading.get('extra')
                    )
                )

            if telemetry_create_list:
                telemetry_command_provider.create_multiple_telemetry_data(db=db, obj_in_list=telemetry_create_list)

            # 8단계: 기기 상태 업데이트
            if snapshot.captured_at:
                device.last_seen_at = snapshot.captured_at
            else:
                device.last_seen_at = datetime.now(timezone.utc)
                
            db.commit()
            return True, None

        except Exception as e:
            logger.error(f"Policy Ingestion Failed: {e}", exc_info=True)
            db.rollback()
            return False, str(e)

    # ... 이하 _parse_timestamp, _reconcile_sequence 등 헬퍼 함수들 (다니엘님 코드와 동일) ...
    def _parse_timestamp(self, ts_value: Union[str, int, float, None]) -> datetime:
        if ts_value is None: return datetime.now(timezone.utc)
        try:
            if isinstance(ts_value, (int, float)):
                if ts_value > 10000000000: ts_value = ts_value / 1000.0
                return datetime.fromtimestamp(ts_value, timezone.utc)
            if isinstance(ts_value, str):
                if ts_value.endswith('Z'): ts_value = ts_value[:-1] + '+00:00'
                return datetime.fromisoformat(ts_value)
        except: pass
        return datetime.now(timezone.utc)

    def _reconcile_sequence(self, db: Session, device_id: int, instance_name: str, current_full_seq: int):
        last_full_seq = sequence_cache_command_provider.get_last_seq(device_id, instance_name)
        current_date, current_seq = divmod(current_full_seq, 100000)
        if last_full_seq is not None:
            last_full_seq = int(last_full_seq)
            last_date, last_seq = divmod(last_full_seq, 100000)
            if current_date == last_date and current_seq > last_seq + 1:
                self._log_gap_to_audit(db, device_id, instance_name, current_date, last_seq + 1, current_seq - 1)
        sequence_cache_command_provider.set_last_seq(device_id, instance_name, current_full_seq)

    def _log_gap_to_audit(self, db: Session, device_id: int, instance_name: str, date: int, start: int, end: int):
        try:
            audit_command_provider.log(
                db=db, event_type="DATA_GAP_DETECTED",
                description=f"Gap in {instance_name}", target_device_id=device_id,
                details={"date": date, "instance_name": instance_name, "start_seq": start, "end_seq": end, "recovery_status": "PENDING"}
            )
            db.commit() 
        except: pass

    def _log_audit_failure(self, db: Session, event_type: str, description: str, details: dict):
        try:
            audit_command_provider.log(db=db, event_type=event_type, description=description, details=details)
            db.commit()
        except: pass

telemetry_ingestion_policy = TelemetryIngestionPolicy()