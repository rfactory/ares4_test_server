from app.domains.services.storage.services.storage_service import storage_service

class StorageProvider:
    """
    내부 도메인들이 StorageService를 직접 참조하지 않고 
    정해진 규칙에 따라 파일을 업로드할 수 있게 하는 인터페이스입니다.
    """
    def upload_image(self, data: bytes, device_uuid: str) -> str:
        """
        이미지 데이터를 받아 기기별 시각 데이터 폴더(devices/{uuid}/vision)에 저장합니다.
        """
        # 비즈니스 규칙: 기기 UUID별로 폴더를 나누어 관리
        folder_path = f"devices/{device_uuid}/vision"
        
        # 실제 서비스 호출
        return storage_service.save_file(
            file_data=data, 
            folder=folder_path, 
            extension="jpg"
        )

# 싱글턴으로 제공
storage_provider = StorageProvider()