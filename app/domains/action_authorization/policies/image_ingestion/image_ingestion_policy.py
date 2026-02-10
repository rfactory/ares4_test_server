import logging
import base64
import os
import json
import redis
from typing import Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

# --- Inter-Domain Providers (정보 징집 및 집행) ---
from app.domains.inter_domain.device_management.device_query_provider import device_management_query_provider
from app.domains.inter_domain.image_registry.image_command_provider import image_command_provider
from app.domains.inter_domain.storage.storage_service_provider import storage_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
from app.domains.inter_domain.observation.observation_snapshot_command_provider import observation_snapshot_command_provider
from app.domains.inter_domain.batch_tracker.batch_status_command_provider import batch_status_command_provider

# --- Validator Provider (판단 요청 창구) ---
from app.domains.inter_domain.validators.image_ingestion.image_ingestion_validator_provider import image_ingestion_validator_provider

logger = logging.getLogger(__name__)

# 인프라 설정
REDIS_URL = "redis://localhost:6379/0"
IMAGE_QUEUE_NAME = "ares4_image_jobs"
LANDING_ZONE_PATH = "/tmp/ares4_landing_zone"
redis_client = redis.from_url(REDIS_URL)

class ImageIngestionPolicy:
    def ingest(self, db: Session, *, topic: str = None, payload: Dict, file_data: Optional[bytes] = None) -> Tuple[bool, Optional[str]]:
        """
        [Step 1: Ingest] 배달부 및 조율자 역할
        - 정보를 수집하여 심판(Validator)에게 던지고, 승인 시 큐에 투척합니다.
        """
        try:
            # 1. 정보 징집 (Data Gathering)
            image_bytes = file_data or self._decode_image(payload.get("image_data"))
            if not image_bytes:
                return False, "Image data is missing or corrupted."

            device_uuid = payload.get("device_uuid") or (topic.split("/")[1] if topic else None)
            # 심판에게 보낼 기기 객체 확보
            device = device_management_query_provider.get_device_by_uuid(db, current_uuid=device_uuid)

            # 2. 판단 요청 (Validation)
            # Validator Provider에게 Yes/No 판결을 의뢰함
            is_valid, error_msg = image_ingestion_validator_provider.validate_all(
                device=device,
                image_bytes=image_bytes,
                payload=payload
            )
            
            if not is_valid:
                logger.warning(f"⚠️ [Ingest Denied] Device: {device_uuid} | Reason: {error_msg}")
                return False, error_msg

            # 3. 집행 (Execution: Landing Zone 저장 & Queue 투척)
            os.makedirs(LANDING_ZONE_PATH, exist_ok=True)
            temp_file_name = f"{device_uuid}_{datetime.now().timestamp()}.jpg"
            temp_full_path = os.path.join(LANDING_ZONE_PATH, temp_file_name)
            
            with open(temp_full_path, "wb") as f:
                f.write(image_bytes)

            # 큐에는 원본 데이터 대신 임시 경로와 메타데이터만 담아 가볍게 보냅니다.
            clean_payload = {k: v for k, v in payload.items() if k != "image_data"}
            job_ticket = {
                "device_uuid": device_uuid,
                "temp_file_path": temp_full_path,
                "payload": clean_payload
            }
            redis_client.rpush(IMAGE_QUEUE_NAME, json.dumps(job_ticket))

            logger.info(f"📤 [Enqueued] Verified image job for {device_uuid} pushed to queue.")
            return True, None

        except Exception as e:
            logger.error(f"🔥 [Ingest Fatal] Policy execution failed: {e}", exc_info=True)
            return False, str(e)

    def process_async_job(self, db: Session, *, device_uuid: str, temp_file_path: str, payload: Dict) -> Tuple[bool, Optional[str]]:
        """
        [Step 2: Process] 워커 전용 실행 로직
        - 워커 스크립트가 호출하며, 실제 물리/DB 저장 및 장부 업데이트를 완료합니다.
        """
        try:
            # 1. 실행 준비
            device = device_management_query_provider.get_device_by_uuid(db, current_uuid=device_uuid)
            if not device: return False, "Device not found during async processing."

            with open(temp_file_path, "rb") as f:
                image_bytes = f.read()

            # 2. 물리 저장 (S3 등)
            uploaded_path = storage_provider.upload_image(image_bytes, device_uuid)
            
            # 3. 스냅샷 확보
            snapshot = observation_snapshot_command_provider.get_or_create_snapshot(
                db=db,
                snapshot_id=payload.get("snapshot_id"),
                system_unit_id=device.system_unit_id,
                observation_type="IMAGE"
            )

            # 4. 이미지 레코드 생성
            image_command_provider.create_image_record(
                db=db,
                snapshot_id=snapshot.id,
                device_id=device.id,
                file_path=uploaded_path,
                metadata=payload
            )

            # 5. [추가] 배치 상태 장부 업데이트
            # 워커가 일을 하나 끝냈으므로 장부에 기록하여 진행률을 올립니다.
            batch_id = payload.get("batch_id")
            if batch_id:
                batch_status_command_provider.mark_item_processed(db, batch_id=batch_id)

            # 6. 기기 상태 업데이트 및 감사 로그 기록
            device.last_seen_at = datetime.now()
            audit_command_provider.log(
                db=db,
                event_type="IMAGE_INGESTED",
                description=f"Async Ingested for Device: {device_uuid}",
                target_device=device,
                details={"snapshot_id": payload.get("snapshot_id"), "file_path": uploaded_path}
            )
            
            # 7. 최종 트랜잭션 확정 (Snapshot + Image + BatchCount + Audit)
            db.commit() 

            # 8. 성공 시에만 임시 파일 삭제
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

            return True, None

        except Exception as e:
            logger.error(f"❌ [Async Process Error] {e}", exc_info=True)
            db.rollback()
            return False, str(e)

    def _decode_image(self, raw_data: Any) -> Optional[bytes]:
        """Base64/바이너리 통합 디코딩 헬퍼"""
        if isinstance(raw_data, str):
            try: return base64.b64decode(raw_data)
            except: return None
        return raw_data if isinstance(raw_data, bytes) else None

image_ingestion_policy = ImageIngestionPolicy()