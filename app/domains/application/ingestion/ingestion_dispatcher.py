import logging
from sqlalchemy.orm import Session
from typing import Tuple, Optional, Dict

from app.domains.inter_domain.policies.telemetry_ingestion.telemetry_ingestion_provider import telemetry_ingestion_policy_provider
from app.domains.inter_domain.policies.image_ingestion.image_ingestion_provider import image_ingestion_policy_provider

logger = logging.getLogger(__name__)

class IngestionDispatcher:
    def dispatch(self, db: Session, *, topic: str, payload: Dict) -> Tuple[bool, Optional[str]]:
        # 1. 데이터의 성격 파악 (어느 창구로 보낼지만 결정)
        data_type = self._identify_data_type(topic, payload)
        
        # 2. [Ares Aegis] 각 전문가에게 '원본 데이터셋'을 통째로 배달
        # 이제 배달부는 토픽을 쪼개거나 내용을 디코딩하지 않습니다.
        if data_type == "TELEMETRY":
            return telemetry_ingestion_policy_provider.ingest(
                db=db, 
                topic=topic,   # 토픽 파싱은 정책 내부에서 수행하도록 위임
                payload=payload
            )
            
        elif data_type == "IMAGE":
            return image_ingestion_policy_provider.ingest(
                db=db,
                topic=topic, 
                payload=payload,
                file_data=None  # Webhook 유입임을 알림
            )
            
        return False, f"Unknown data type for topic: {topic}"

    def _identify_data_type(self, topic: str, payload: Dict) -> str:
        t_lower = topic.lower()
        if "telemetry" in t_lower: return "TELEMETRY"
        if "image" in t_lower or "vision" in t_lower: return "IMAGE"
        return str(payload.get("type", "UNKNOWN")).upper()

ingestion_dispatcher = IngestionDispatcher()