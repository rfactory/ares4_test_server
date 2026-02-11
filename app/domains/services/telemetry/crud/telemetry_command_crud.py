from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from typing import List, Dict
from app.models.events_logs.telemetry_data import TelemetryData
from app.models.events_logs.telemetry_metadata import TelemetryMetadata
from ..schemas.telemetry_command import TelemetryCommandDataCreate

class CRUDTelemetryCommand:
    def create_multiple(self, db: Session, *, obj_in_list: List[TelemetryCommandDataCreate]) -> List[TelemetryData]:
        # 1. 모든 부모 TelemetryData 객체 생성 (스키마의 component_name이 모델에 전달됨)
        db_telemetry_list = [
            TelemetryData(**obj_in.model_dump(exclude={"metadata_items"})) 
            for obj_in in obj_in_list
        ]
        
        db.add_all(db_telemetry_list)
        db.flush()

        # 2. 자식 TelemetryMetadata 객체 생성
        metadata_to_add = []
        for i, obj_in in enumerate(obj_in_list):
            if obj_in.metadata_items:
                db_telemetry = db_telemetry_list[i]
                for meta_item in obj_in.metadata_items:
                    db_metadata = TelemetryMetadata(
                        telemetry_data_id=db_telemetry.id, 
                        **meta_item.model_dump()
                    )
                    metadata_to_add.append(db_metadata)
        
        if metadata_to_add:
            db.add_all(metadata_to_add)

        return db_telemetry_list
    
    def bulk_upsert(self, db: Session, *, obj_in_list: List[Dict]) -> int:
        """[Ares Aegis] DB 레벨 고속 벌크 업서트"""
        if not obj_in_list:
            return 0

        stmt = pg_insert(TelemetryData).values(obj_in_list)

        # [핵심 수정] 어떤 부품(component_name)에서 온 데이터인지도 중복 체크 기준에 포함해야 합니다.
        stmt = stmt.on_conflict_do_nothing(
            index_elements=['device_id', 'component_name', 'metric_name', 'captured_at']
        )

        result = db.execute(stmt)
        return result.rowcount

telemetry_crud_command = CRUDTelemetryCommand()