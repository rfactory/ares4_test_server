from typing import Tuple, Optional, Any

class ImageIngestionValidator:
    def validate_all(
        self, 
        *, 
        device: Optional[Any], 
        image_bytes: bytes, 
        payload: dict
    ) -> Tuple[bool, Optional[str]]:
        """지휘관이 준 데이터만 보고 Yes/No를 판단함"""
        
        # 1. 기기 존재 및 상태 확인 (객체가 있으면 True)
        if not device:
            return False, "Target device not found or unauthorized."

        # 2. 필수 필드 검증
        if not payload.get("snapshot_id"):
            return False, "Missing mandatory field: snapshot_id"

        # 3. 이미지 형식 확인
        if not self.is_valid_format(image_bytes):
            return False, "Invalid image format: Only JPEG/PNG supported."
            
        # 4. 이미지 크기 확인
        if not self.is_safe_size(image_bytes, max_mb=10):
            return False, "Image size exceeds allowed limit (10MB)."

        return True, None

    def is_valid_format(self, data: bytes) -> bool:
        return data.startswith(b'\xff\xd8\xff') or data.startswith(b'\x89PNG\r\n\x1a\n')

    def is_safe_size(self, data: bytes, max_mb: int) -> bool:
        return len(data) <= max_mb * 1024 * 1024

image_ingestion_validator = ImageIngestionValidator()