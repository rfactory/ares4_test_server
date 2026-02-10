from sqlalchemy.orm import Session
from typing import Dict, Any, Tuple, Optional
from app.domains.action_authorization.policies.image_ingestion.image_ingestion_policy import image_ingestion_policy

class ImageIngestionPolicyProvider:
    """
    외부 도메인(Dispatcher 등)에서 이미지 인제션 정책을 
    안전하게 호출할 수 있도록 돕는 창구입니다.
    """
    def ingest(
        self, 
        db: Session, 
        *, 
        device_uuid_str: str, 
        payload: Dict[str, Any], 
        file_data: bytes
    ) -> Tuple[bool, Optional[str]]:
        # 실제 정책(뇌)에게 실행을 위임합니다.
        return image_ingestion_policy.ingest(
            db=db,
            device_uuid_str=device_uuid_str,
            payload=payload,
            file_data=file_data
        )

image_ingestion_policy_provider = ImageIngestionPolicyProvider()