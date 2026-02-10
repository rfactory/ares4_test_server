from typing import Tuple, Optional, List, Dict, Any

class BatchIngestionValidator:
    def validate_batch_request(
        self, 
        *, 
        device: Optional[Any], 
        telemetry_data: List[Dict[str, Any]], 
        image_files: List[Any]
    ) -> Tuple[bool, Optional[str]]:
        """지휘관이 준 배치 보따리를 보고 입국 허가 여부만 판단"""
        
        # 1. 기기 신분 확인
        if not device:
            return False, "Target device not found or unauthorized for batch ingestion."

        # 2. 배치 규모 확인 (너무 크면 시스템 과부하 방지를 위해 거절)
        if len(telemetry_data) > 10000:
            return False, "Batch telemetry size exceeds limit (Max: 10,000)."
        
        if len(image_files) > 1000:
            return False, "Batch image count exceeds limit (Max: 1,000)."

        # 3. 데이터 최소 요건 확인
        if not telemetry_data and not image_files:
            return False, "Batch payload is empty."

        return True, None

batch_ingestion_validator = BatchIngestionValidator()