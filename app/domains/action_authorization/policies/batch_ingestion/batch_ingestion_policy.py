import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import UploadFile

# --- Inter-Domain Providers (정보 징집 및 집행) ---
from app.domains.inter_domain.device_management.device_query_provider import device_management_query_provider
from app.domains.inter_domain.telemetry.telemetry_command_provider import telemetry_command_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
from app.domains.inter_domain.batch_tracker.batch_status_command_provider import batch_status_command_provider

# --- Action Authorization Policies & Validators ---
from app.domains.action_authorization.policies.image_ingestion.image_ingestion_policy import image_ingestion_policy
from app.domains.inter_domain.validators.batch_ingestion.batch_ingestion_validator_provider import batch_ingestion_validator_provider

logger = logging.getLogger("BatchIngestionPolicy")

class BatchIngestionPolicy:
    async def handle_batch(
        self, 
        db: Session, 
        *, 
        device_uuid: str, 
        telemetry_data: List[Dict[str, Any]], 
        image_files: List[UploadFile]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        [Ares Aegis] 배치 통합 지휘 로직
        - 정보를 소집하고 심판의 판결을 받은 뒤, 각 엔진(Bulk/Queue)에 분배하고 장부를 기록합니다.
        """
        try:
            # 1. 정보 징집 (Data Gathering)
            device = device_management_query_provider.get_device_by_uuid(db, current_uuid=device_uuid)

            # 2. 판단 요청 (Validation)
            # 심판(Validator)에게 이 거대한 보따리를 받아도 될지 판결을 의뢰합니다.
            is_valid, error_msg = batch_ingestion_validator_provider.validate_all(
                device=device,
                telemetry_data=telemetry_data,
                image_files=image_files
            )
            if not is_valid:
                logger.warning(f"🚫 [Batch Denied] Device: {device_uuid} | Reason: {error_msg}")
                return False, error_msg, {}

            # 3. [중요] 배치 장부 개설 (Command)
            # 워커들이 보고할 수 있도록 Batch ID를 먼저 생성하고 DB에 등록합니다.
            batch_id = batch_status_command_provider.register_new_batch(
                db, 
                device_id=device.id, 
                total_count=len(image_files)
            )

            logger.info(f"🏰 [Batch Authorized] Device: {device_uuid} | Batch ID: {batch_id} | Processing...")

            # 4. 집행 A: 텔레메트리 벌크 업서트 (즉시 처리)
            # 8,000건의 데이터를 단 한 번의 SQL 쿼리로 격파합니다.
            inserted_count = 0
            if telemetry_data:
                inserted_count = telemetry_command_provider.bulk_upsert_telemetry_data(
                    db=db,
                    device_id=device.id,
                    telemetry_list=telemetry_data
                )

            # 5. 집행 B: 이미지 비동기 큐 배분 (이미지 정책에 위임)
            queued_images = 0
            for img in image_files:
                # [중요] 생성한 batch_id를 페이로드에 심어줍니다. 워커의 보고를 위해서입니다.
                img_payload = {
                    "device_uuid": device_uuid,
                    "batch_id": batch_id,
                    "snapshot_id": f"batch_{device.id}_{img.filename}", 
                    "captured_at": telemetry_data[0].get("captured_at") if telemetry_data else None
                }
                
                # 이미지 부서(Policy)의 입구로 전달하여 큐에 투척
                success, _ = image_ingestion_policy.ingest(
                    db=db,
                    payload=img_payload,
                    file_data=await img.read()
                )
                if success:
                    queued_images += 1

            # 6. 감사 로그 기록 (Audit)
            # 성문의 기록관에게 배치가 공식적으로 시작되었음을 남깁니다.
            audit_command_provider.log(
                db=db,
                event_type="BATCH_INGESTION_STARTED",
                description=f"Batch {batch_id} started. Telemetry: {inserted_count}, Images: {queued_images}",
                target_device=device,
                details={
                    "batch_id": batch_id,
                    "telemetry_count": inserted_count,
                    "image_count": queued_images
                }
            )

            # 7. 최종 확정 (Commit)
            # 장부 개설 + 텔레메트리 저장 + 감사 로그를 단 하나의 트랜잭션으로 묶어 확정합니다.
            db.commit() 

            logger.info(f"✅ [Batch Success] Batch ID: {batch_id} | Telemetry: {inserted_count} | Images: {queued_images}")

            return True, "Batch processed and images queued successfully.", {
                "batch_id": batch_id,
                "telemetry_processed": inserted_count,
                "images_queued": queued_images,
                "purge_allowed": False # 아직 워커가 작업 중이므로 초기값은 False
            }

        except Exception as e:
            # 하나라도 실패하면 장부 개설부터 텔레메트리까지 모두 없던 일로 돌립니다.
            db.rollback()
            logger.error(f"🔥 [Batch Fatal] Distribution failed: {e}", exc_info=True)
            return False, str(e), {}

batch_ingestion_policy = BatchIngestionPolicy()