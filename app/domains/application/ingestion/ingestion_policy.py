import logging
from sqlalchemy.orm import Session
from typing import Tuple, Optional, Dict
from uuid import UUID

from app.domains.application.ingestion.ingestion_dispatcher import ingestion_dispatcher
from app.domains.inter_domain.policies.telemetry_ingestion.telemetry_ingestion_provider import telemetry_ingestion_policy_provider
from app.domains.inter_domain.policies.image_ingestion.image_ingestion_provider import image_ingestion_policy_provider

logger = logging.getLogger(__name__)

class IngestionPolicy:
    def handle_webhook_ingestion(self, db: Session, *, topic: str, payload: Dict) -> Tuple[bool, Optional[str]]:
        try:
            topic_parts = topic.split("/")
            device_uuid_str = topic_parts[1]
        except (IndexError, AttributeError):
            return False, f"Invalid topic: {topic}"

        # [ImportError 해결] 지연 임포트 및 정확한 명칭 사용
        from app.domains.inter_domain.device_management.device_internal_query_provider import device_internal_query_provider
        from app.domains.inter_domain.device_management.device_command_provider import device_management_command_provider
        from app.domains.services.device_management.schemas.device_command import DeviceUpdate
        from app.core.config import settings

        # 1. 장치 조회
        device = device_internal_query_provider.get_device_with_secret_by_uuid(
            db, current_uuid=UUID(device_uuid_str)
        )

        if not device:
            return False, f"Device not found in DB: {device_uuid_str}"

        # 2. [근본 해결] 자동 등록(Auto-Provisioning)
        # mTLS는 이미 통과했으므로 신뢰할 수 있음. DB에 키가 없다면 서버 설정 키로 등록.
        if device.hmac_secret_key is None:
            logger.info(f"🚀 [Auto-Enroll] 장치 {device_uuid_str} 키 자동 등록 중...")
            
            # settings.ARES4_HMAC_KEY를 사용하여 업데이트
            update_data = DeviceUpdate(hmac_secret_key=settings.ARES4_HMAC_KEY)
            
            # [수정 포인트] actor_user=None 추가 (시스템 자동 작업임을 명시)
            device_management_command_provider.update_device(
                db, 
                device_id=device.id, 
                obj_in=update_data,
                actor_user=None  # 👈 이 인자가 누락되어 500 에러가 났던 것입니다.
            )
            db.commit()
            
            # 등록 후 최신 정보 재로드
            device = device_internal_query_provider.get_device_with_secret_by_uuid(
                db, current_uuid=UUID(device_uuid_str)
            )

        # 3. 데이터 처리 분기
        data_type = ingestion_dispatcher._identify_data_type(topic, payload)
        
        if data_type == "IMAGE":
            return image_ingestion_policy_provider.ingest(
                db=db, device_uuid_str=device_uuid_str, topic=topic, payload=payload, file_data=None
            )
        elif data_type == "TELEMETRY":
            return telemetry_ingestion_policy_provider.ingest(
                db=db, device_uuid_str=device_uuid_str, topic=topic, payload=payload
            )
        
        return False, f"Unsupported type: {data_type}"

    def handle_image_upload(self, db: Session, *, device_uuid_str: str, payload: Dict, file_data: bytes) -> Tuple[bool, Optional[str]]:
        return image_ingestion_policy_provider.ingest(
            db=db, device_uuid_str=device_uuid_str, payload=payload, file_data=file_data
        )

ingestion_policy = IngestionPolicy()