# --- Command-related CRUD ---
# 이 파일은 데이터의 상태를 변경하는 DB 작업을 직접 수행하는 'Command' CRUD 클래스를 정의합니다.

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from typing import List, Dict
from app.models.events_logs.telemetry_data import TelemetryData
from app.models.events_logs.telemetry_metadata import TelemetryMetadata
from ..schemas.telemetry_command import TelemetryCommandDataCreate

class CRUDTelemetryCommand:
    def create_multiple(self, db: Session, *, obj_in_list: List[TelemetryCommandDataCreate]) -> List[TelemetryData]:
        # 1. 먼저 모든 부모 TelemetryData 객체를 생성합니다.
        db_telemetry_list = [
            TelemetryData(**obj_in.model_dump(exclude={"metadata_items"})) 
            for obj_in in obj_in_list
        ]
        
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
                        telemetry_data_id=db_telemetry.id, 
                        **meta_item.model_dump() # .dict() 대신 .model_dump()
                    )
                    metadata_to_add.append(db_metadata)
        
        # 5. 모든 메타데이터 객체들을 세션에 추가합니다.
        if metadata_to_add:
            db.add_all(metadata_to_add)

        return db_telemetry_list
    
    def bulk_upsert(self, db: Session, *, obj_in_list: List[Dict]) -> int:
        """
        [Ares Aegis] DB 레벨 고속 벌크 업서트
        - 중복 데이터(기기ID + 측정시간 + 항목명) 발생 시 무시(DO NOTHING).
        - 대량 배치 전송 시 성능 병목을 제거하는 핵심 전술.
        """
        if not obj_in_list:
            return 0

        # 1. PostgreSQL 전용 INSERT 구문 생성
        stmt = pg_insert(TelemetryData).values(obj_in_list)

        # 2. 충돌 제어: device_id, captured_at, metric_name이 겹치면 무시
        # 주의: DB 모델에 해당 컬럼들에 대한 Unique Constraint(UniqueIndex)가 설정되어 있어야 합니다.
        stmt = stmt.on_conflict_do_nothing(
            index_elements=['device_id', 'captured_at', 'metric_name']
        )

        # 3. 쿼리 실행 및 영향받은 행 수 반환
        result = db.execute(stmt)
        return result.rowcount

telemetry_crud_command = CRUDTelemetryCommand()