import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import Tuple, Optional, Dict, Any, TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from app.models.objects.device import Device as Device

# --- Providers (Inter-Domain) ---
from app.domains.inter_domain.device_management.device_internal_query_provider import device_internal_query_provider
from app.domains.inter_domain.validators.cluster_authority.master_authority_validator_provider import master_authority_validator_provider
from app.domains.inter_domain.validators.cluster_authority.cluster_membership_validator_provider import cluster_membership_validator_provider
from app.domains.inter_domain.validators.hmac_integrity.provider import hmac_integrity_validator_provider
from app.domains.inter_domain.telemetry.telemetry_command_provider import telemetry_command_provider
from app.domains.inter_domain.device_management.device_command_provider import device_management_command_provider

logger = logging.getLogger(__name__)

class TelemetryIngestionPolicy:
    """
    [The Orchestrator] 텔레메트리 수신 정책:
    각 도메인 서비스와 검증기를 지휘하여 클러스터 데이터를 안전하게 수신합니다.
    """
    def ingest(self, db: Session, *, device_uuid_str: str, topic: str, payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        try:
            # 1. [Query Service] 문맥 확보 (조회는 Query의 권한)
            master_device: Optional["Device"] = device_internal_query_provider.get_device_with_secret_by_uuid(db, UUID(device_uuid_str))
            system_unit = master_device.system_unit if master_device else None

            # 2. [Validators] 판결 요청 (판단은 Validator의 권한)
            # 2-1. 마스터 권한 검증
            is_valid, err = master_authority_validator_provider.validate(master_device, system_unit)
            if not is_valid: return False, err

            # 2-2. HMAC 무결성 검증
            is_valid, err = hmac_integrity_validator_provider.validate(db=db, device=master_device, payload=payload)
            if not is_valid: return False, err

            # 2-3. 클러스터 멤버십 검증
            node_uuids = [n.get('device_uuid') for n in payload.get('nodes', [])]
            is_valid, invalid_nodes = cluster_membership_validator_provider.validate_nodes(node_uuids, system_unit)
            if not is_valid:
                return False, f"Membership Violation: Invalid nodes {invalid_nodes}"

            # 3. [Command Service] 작업 하달 (수정/저장은 Command의 권한)
            # 데이터 파쇄(Shredding) 및 DB 저장은 Command Service 내부에서 수행됩니다.
            telemetry_command_provider.process_cluster_batch_ingestion(
                db=db,
                system_unit=system_unit,
                payload=payload
            )

            # 4. [Command Service] 상태 업데이트
            device_management_command_provider.update_last_seen_at(db, master_device.id)

            db.commit()
            return True, None

        except Exception as e:
            logger.error(f"Policy Orchestration Failed: {e}", exc_info=True)
            db.rollback()
            return False, str(e)

telemetry_ingestion_policy = TelemetryIngestionPolicy()