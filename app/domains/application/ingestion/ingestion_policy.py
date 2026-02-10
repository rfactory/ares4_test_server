import logging
from sqlalchemy.orm import Session
from typing import Tuple, Optional, Dict

# --- 하위 전략 및 배달부 ---
from app.domains.application.ingestion.ingestion_dispatcher import ingestion_dispatcher
from app.domains.inter_domain.policies.telemetry_ingestion.telemetry_ingestion_provider import telemetry_ingestion_policy_provider
from app.domains.inter_domain.policies.image_ingestion.image_ingestion_provider import image_ingestion_policy_provider

logger = logging.getLogger(__name__)

class IngestionPolicy:
    """
    [Ares Aegis] 수집 통합 지휘관
    모든 경로(Webhook 등)에서 들어오는 데이터 수집의 최종 의사결정을 담당합니다.
    """

    def handle_webhook_ingestion(self, db: Session, *, topic: str, payload: Dict) -> Tuple[bool, Optional[str]]:
        # 1. 토픽에서 device_uuid_str 추출 (구조: ares4/{uuid}/telemetry)
        try:
            topic_parts = topic.split("/")
            device_uuid_str = topic_parts[1]
        except (IndexError, AttributeError):
            error_msg = f"Invalid topic structure for UUID extraction: {topic}"
            logger.error(f"INGESTION_POLICY: {error_msg}")
            return False, error_msg

        data_type = ingestion_dispatcher._identify_data_type(topic, payload)
        
        if data_type == "IMAGE":
            if not payload.get("image_data") and "vision" not in topic:
                error_msg = "Image ingestion triggered but 'image_data' is missing in payload."
                logger.warning(f"INGESTION_POLICY: {error_msg}")
                return False, error_msg

            # 추출한 device_uuid_str을 함께 전달합니다.
            return image_ingestion_policy_provider.ingest(
                db=db, 
                device_uuid_str=device_uuid_str, # 추가
                topic=topic, 
                payload=payload, 
                file_data=None
            )
            
        elif data_type == "TELEMETRY":
            if "data" not in payload:
                return False, "Telemetry data field is missing."
                
            # 추출한 device_uuid_str을 전달하여 TypeError를 해결합니다.
            return telemetry_ingestion_policy_provider.ingest(
                db=db, 
                device_uuid_str=device_uuid_str, # 추가 (핵심 수정 사항)
                topic=topic, 
                payload=payload
            )
        
        return False, f"Unsupported data type: {data_type}"
    
    def handle_image_upload(self, db: Session, *, device_uuid_str: str, payload: Dict, file_data: bytes) -> Tuple[bool, Optional[str]]:
        """HTTP 업로드를 통해 들어온 이미지 데이터를 수집합니다."""
        return image_ingestion_policy_provider.ingest(
            db=db, 
            device_uuid_str=device_uuid_str, 
            payload=payload, 
            file_data=file_data
        )

# 싱글톤 인스턴스 생성
ingestion_policy = IngestionPolicy()