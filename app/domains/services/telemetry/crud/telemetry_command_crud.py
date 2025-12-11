# --- Command-related CRUD ---
# 이 파일은 데이터의 상태를 변경하는 DB 작업을 직접 수행하는 'Command' CRUD 클래스를 정의합니다.

from sqlalchemy.orm import Session
from typing import List
from app.models.events_logs.telemetry_data import TelemetryData
from app.models.events_logs.telemetry_metadata import TelemetryMetadata
from ..schemas.telemetry_command import TelemetryCommandDataCreate

class CRUDTelemetryCommand:
    def create_multiple(self, db: Session, *, obj_in_list: List[TelemetryCommandDataCreate]) -> List[TelemetryData]:
        # 1. 먼저 모든 부모 TelemetryData 객체를 생성합니다.
        db_telemetry_list = [TelemetryData(**obj_in.dict(exclude={"metadata_items"})) for obj_in in obj_in_list]
        
        # 2. 세션에 추가합니다.
        db.add_all(db_telemetry_list)
        
        # 3. 세션을 한 번만 flush하여 생성된 모든 객체의 ID를 가져옵니다.
        db.flush()

        # 4. 자식 TelemetryMetadata 객체들을 생성합니다.
        metadata_to_add = []
        for i, obj_in in enumerate(obj_in_list):
            if obj_in.metadata_items:
                db_telemetry = db_telemetry_list[i]
                for meta_item in obj_in.metadata_items:
                    db_metadata = TelemetryMetadata(
                        telemetry_data_id=db_telemetry.id, **meta_item.dict()
                    )
                    metadata_to_add.append(db_metadata)
        
        # 5. 모든 메타데이터 객체들을 세션에 추가합니다.
        if metadata_to_add:
            db.add_all(metadata_to_add)

        return db_telemetry_list

telemetry_crud_command = CRUDTelemetryCommand()