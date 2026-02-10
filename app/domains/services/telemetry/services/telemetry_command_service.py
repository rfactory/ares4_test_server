# --- Command-related Service ---
# 이 파일은 데이터의 상태를 변경하는 'Command' 성격의 비즈니스 로직을 담당합니다.
# [DESIGN PRINCIPLE] 텔레메트리 데이터는 기기로부터 온 '진실된 정보'로 간주됩니다.
# 따라서 이 서비스는 데이터 생성(Create) 기능만 제공하며, 수정(Update) 및 삭제(Delete) 기능은 의도적으로 배제되었습니다.

from sqlalchemy.orm import Session
from typing import List, Dict

from app.models.events_logs.telemetry_data import TelemetryData
from ..crud.telemetry_command_crud import telemetry_crud_command
from ..schemas.telemetry_command import TelemetryCommandDataCreate

class TelemetryCommandService:
    def create_multiple_telemetry(self, db: Session, *, obj_in_list: List[TelemetryCommandDataCreate]) -> List[TelemetryData]:
        """여러 텔레메트리 데이터를 벌크로 생성합니다."""
        new_telemetry_list = telemetry_crud_command.create_multiple(db, obj_in_list=obj_in_list)
        # db.commit()    ← 삭제
        # db.refresh()   ← 삭제
        # → Policy에서 한 번만 커밋하면 됨
        return new_telemetry_list
    
    def bulk_upsert_telemetry(self, db: Session, *, device_id: int, telemetry_list: List[Dict]) -> int:
        """
        [Ares Aegis] 고속 벌크 업서트
        - ON CONFLICT DO NOTHING 전략을 사용하여 중복 시퀀스는 자동으로 스킵합니다.
        - 수천 건의 데이터를 단일 쿼리로 처리하여 성능을 극대화합니다.
        - 반환값: 실제로 삽입된 행(Row)의 수 (DB 드라이버 지원 시)
        """
        if not telemetry_list:
            return 0
        
        # 1. 딕셔너리 리스트에 device_id 강제 주입 (보안 및 정합성 보장)
        for data in telemetry_list:
            data['device_id'] = device_id
            
        # 2. CRUD 계층의 벌크 업서트 호출
        # 이 메서드는 내부적으로 INSERT ... ON CONFLICT DO NOTHING을 실행해야 합니다.
        affected_rows = telemetry_crud_command.bulk_upsert(db, obj_in_list=telemetry_list)
        
        return affected_rows

telemetry_command_service = TelemetryCommandService()
