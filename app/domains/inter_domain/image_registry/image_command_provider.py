from app.domains.services.image_registry.services.image_service import image_service

class ImageCommandProvider:
    """
    다른 도메인(Policy 등)에서 이미지 등록을 요청할 때 사용하는 전용 창구입니다.
    """
    def create_image_record(
        self,
        db,
        *,
        snapshot_id: str,
        device_id: int,
        system_unit_id: int,
        file_path: str,
        metadata: dict
        ):
        """
        ImageService를 호출하여 장부를 작성합니다.
        """
        return image_service.create_registry_record(
            db,
            snapshot_id=snapshot_id,
            device_id=device_id,
            system_unit_id=system_unit_id,
            storage_path=file_path,
            image_metadata=metadata # JSONB 컬럼에 담깁니다.
        )

image_command_provider = ImageCommandProvider()