# 파일 경로: server2/app/domains/action_authorization/policies/telemetry_ingestion/telemetry_ingestion_policy.py
import logging
import json
from sqlalchemy.orm import Session
from typing import Tuple, Optional, Dict
from uuid import UUID

# --- Providers ---
# 내부 도메인에서 DeviceWithSecret 스키마(민감 정보 포함)를 조회하기 위한 Provider
from app.domains.inter_domain.device_management.device_internal_query_provider import device_internal_query_provider
# 시스템 지원 부품 정보를 조회하기 위한 Provider
from app.domains.inter_domain.supported_component_management.supported_component_query_provider import supported_component_query_provider

# --- Validator Providers (개별 Validator의 기능을 노출) ---
# 기기 존재 여부를 검증하는 Provider
from app.domains.inter_domain.validators.device_existence.provider import device_existence_validator_provider
# CPU 시리얼을 통해 기기 신원을 검증하는 Provider
from app.domains.inter_domain.validators.cpu_serial.provider import cpu_serial_validator_provider
# HMAC 서명을 통해 메시지 무결성을 검증하는 Provider
from app.domains.inter_domain.validators.hmac_integrity.provider import hmac_integrity_validator_provider
# 특정 부품 인스턴스가 기기에 연결되어 있는지 검증하는 Provider
from app.domains.inter_domain.validators.device_attachment.provider import device_attachment_validator_provider
# 특정 부품이 기기의 하드웨어 설계도와 호환되는지 검증하는 Provider
from app.domains.inter_domain.validators.blueprint_compatibility.provider import blueprint_compatibility_validator_provider

# --- Command Providers (데이터 저장 및 부수 효과 발생) ---
# 텔레메트리 데이터를 저장하기 위한 Provider
from app.domains.inter_domain.telemetry.telemetry_command_provider import telemetry_command_provider
# 모든 작업 완료 후 감사 로그를 기록하기 위한 Provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

# --- Schemas ---
# Provider가 반환하거나, Validator에 전달할 데이터의 타입을 명시하기 위해 사용.
from app.domains.inter_domain.device_management.schemas.device_internal import DeviceWithSecret
from app.domains.inter_domain.telemetry.schemas.telemetry_command import TelemetryCommandDataCreate
# 감사 로그를 남길 때, 행위자(actor)의 타입을 명시하기 위해 사용.
from app.domains.inter_domain.user_identity.schemas.models import User


logger = logging.getLogger(__name__)

class TelemetryIngestionPolicy:
    """
    텔레메트리 수신에 대한 전체 유효성 검사 및 처리 정책을 시행하는 '뇌(Brain)' 역할을 합니다.
    여러 Provider와 Validator를 오케스트레이션합니다.
    """
    def ingest(
        self,
        db: Session,
        *,
        device_uuid_str: str,
        payload: Dict,
        # 감사 로그의 행위자를 기록하기 위한 파라미터.
        # 시스템(기기)이 직접 보낸 메시지일 경우 None이 될 수 있음.
        actor_user: Optional[User] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        들어오는 MQTT 텔레메트리 메시지를 검증하고 처리하는 전체 워크플로우를 담당합니다.
        각 검증 단계는 단일 책임을 가지는 Validator Provider를 통해 위임됩니다.
        """

        # --- 1단계: 기기 존재 여부 검증 (Device Existence Validation) ---
        # 주어진 UUID 문자열이 유효한 형식인지 확인하고, 해당 UUID를 가진 기기가 DB에 존재하는지 검증합니다.
        is_valid, error_msg = device_existence_validator_provider.validate(db=db, device_uuid_str=device_uuid_str)
        if not is_valid:
            logger.warning(f"POLICY: Device existence validation failed for UUID: {device_uuid_str}. Reason: {error_msg}")
            return False, error_msg

        # --- 2단계: 핵심 정보 조회 (Fetch Core Information) ---
        # 불필요한 중복 조회를 방지하기 위해, 이후 Validator들이 필요로 할 정보를 미리 조회합니다.
        # device_internal_query_provider를 사용하여 기기 정보를 상세하게 조회합니다. 이 객체는 cpu_serial, hmac_key_name과 같은 민감한 정보를 포함합니다.
        device = device_internal_query_provider.get_device_with_secret_by_uuid(db, current_uuid=UUID(device_uuid_str))
        # device_existence_validator_provider가 이미 존재 여부를 확인했으므로, 이 시점에서 device가 None일 가능성은 낮습니다.
        # 하지만 방어적 프로그래밍을 위해 한 번 더 확인합니다.
        if not device:
            error_msg = f"Device with UUID '{device_uuid_str}' unexpectedly not found after existence validation."
            logger.critical(f"POLICY_ERROR: {error_msg}")
            return False, error_msg # 이 경우는 심각한 로직 오류를 의미합니다.
        
        # 페이로드에서 component_type을 추출합니다.
        component_type = payload.get("component_type")
        if not component_type:
            error_msg = f"Payload must contain 'component_type' for device {device_uuid_str}."
            logger.warning(f"POLICY: {error_msg}")
            return False, error_msg
        
        # supported_component_query_provider를 통해 해당 component_type에 대한 SupportedComponent 정보를 조회합니다.
        # 이 객체는 이후 Validator들에게 전달되어 사용됩니다.
        supported_component = supported_component_query_provider.get_by_component_type(db, component_type=component_type)
        if not supported_component:
            error_msg = f"Component type '{component_type}' is not supported by the system for device {device_uuid_str}."
            logger.warning(f"POLICY: {error_msg}")
            return False, error_msg

        # --- 3단계: 신원 및 무결성 검증 (Authenticity and Integrity Validation) ---
        # 3.1: CPU 시리얼을 통한 기기 신원 검증. 기기의 물리적 신원이 페이로드와 일치하는지 확인합니다.
        is_valid, error_msg = cpu_serial_validator_provider.validate(device=device, payload=payload)
        if not is_valid:
            logger.warning(f"POLICY: CPU serial validation failed for device {device_uuid_str}. Reason: {error_msg}")
            return False, error_msg

        # 3.2: HMAC 서명을 통한 메시지 무결성 검증. 메시지가 전송 중 위변조되지 않았는지 확인합니다.
        is_valid, error_msg = hmac_integrity_validator_provider.validate(db=db, device=device, payload=payload)
        if not is_valid:
            logger.warning(f"POLICY: HMAC integrity validation failed for device {device_uuid_str}. Reason: {error_msg}")
            return False, error_msg

        # --- 4단계: 텔레메트리 컨텍스트 유효성 검증 (Telemetry Context Validation) ---
        # 4.1: 부품 인스턴스 연결 확인. 특정 부품 인스턴스가 해당 기기에 올바르게 연결되어 있는지 확인합니다.
        instance_name = payload.get("instance_name")
        if not instance_name:
            error_msg = f"Payload must contain 'instance_name' for device {device_uuid_str}."
            logger.warning(f"POLICY: {error_msg}")
            return False, error_msg
            
        is_valid, error_msg = device_attachment_validator_provider.validate(
            db=db, device_id=device.id, supported_component_id=supported_component.id, instance_name=instance_name
        )
        if not is_valid:
            logger.warning(f"POLICY: Device attachment validation failed for device {device_uuid_str}. Reason: {error_msg}")
            return False, error_msg

        # 4.2: 하드웨어 설계도(Blueprint) 호환성 확인. 부품이 기기의 설계도와 호환되는지 확인합니다.
        is_valid, error_msg = blueprint_compatibility_validator_provider.validate(
            db=db, blueprint_id=device.hardware_blueprint_id, supported_component_id=supported_component.id
        )
        if not is_valid:
            logger.warning(f"POLICY: Blueprint compatibility validation failed for device {device_uuid_str}. Reason: {error_msg}")
            return False, error_msg

        # --- 5단계: 데이터 저장 (Data Ingestion) ---
        # 모든 검증을 통과한 후 텔레메트리 데이터를 DB에 저장합니다.
        data_to_save = payload.get('data', [])
        if not isinstance(data_to_save, list):
            error_msg = "Payload 'data' field must be a list of readings."
            logger.warning(f"POLICY: {error_msg}")
            return False, error_msg

        telemetry_create_list = [
            TelemetryCommandDataCreate(device_id=device.id, component_name=instance_name, **reading) for reading in data_to_save
        ]
        if not telemetry_create_list:
            logger.info(f"POLICY: No telemetry 'data' to save for device {device_uuid_str}.")
            return True, "No data to save."

        created_telemetry = telemetry_command_provider.create_multiple_telemetry_data(db=db, obj_in_list=telemetry_create_list)
        


        # 모든 처리가 성공적으로 완료되었음을 로깅
        logger.info(f"POLICY: Telemetry from device {device_uuid_str} ingested successfully.")
        # 트랜잭션 커밋은 이 Policy를 호출한 상위 Application 계층에서 담당합니다. 이 Policy는 트랜잭션의 일부만 담당합니다.
        return True, None

telemetry_ingestion_policy = TelemetryIngestionPolicy()
