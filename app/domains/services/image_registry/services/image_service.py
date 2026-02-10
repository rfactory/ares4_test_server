from sqlalchemy.orm import Session
from app.models.objects.image_registry import ImageRegistry

class ImageService:
    """
    이미지 자산 등록부(ImageRegistry)에 실제 기록을 남기는 일꾼입니다.
    """
    def create_registry_record(
        self,
        db: Session,
        *,
        snapshot_id: str,
        device_id: int,
        system_unit_id: int,
        storage_path: str,
        image_metadata: dict
        ) -> ImageRegistry:
        """
        저장 경로와 메타데이터를 받아 ImageRegistry 레코드를 생성합니다.
        """
        new_record = ImageRegistry(
            snapshot_id=snapshot_id,
            device_id=device_id,
            system_unit_id=system_unit_id,
            storage_path=storage_path,
            image_metadata=image_metadata
        )
        db.add(new_record)
        
        # ID(PK)를 즉시 확보하여 Snapshot과 연결할 수 있도록 flush합니다.
        db.flush() 
        
        return new_record

image_service = ImageService()