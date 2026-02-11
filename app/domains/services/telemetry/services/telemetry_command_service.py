# C:\vscode project files\Ares4\server2\app\domains\services\telemetry\services\telemetry_command_service.py

from sqlalchemy.orm import Session
from typing import List, Dict

from app.models.events_logs.telemetry_data import TelemetryData
from ..crud.telemetry_command_crud import telemetry_crud_command
# [수정] 중앙 스키마 파일에서만 클래스를 가져옵니다. (중복 정의 삭제)
from ..schemas.telemetry_command import TelemetryCommandDataCreate

class TelemetryCommandService:
    def create_multiple_telemetry(self, db: Session, *, obj_in_list: List[TelemetryCommandDataCreate]) -> List[TelemetryData]:
        """여러 텔레메트리 데이터를 벌크로 생성합니다."""
        # [DESIGN PRINCIPLE] 트랜잭션 커밋은 Policy에서 제어하므로 CRUD만 호출
        return telemetry_crud_command.create_multiple(db, obj_in_list=obj_in_list)
    
    def bulk_upsert_telemetry(self, db: Session, *, device_id: int, telemetry_list: List[Dict]) -> int:
        """[Ares Aegis] 고속 벌크 업서트"""
        if not telemetry_list:
            return 0
        
        # 보안 및 정합성 보장을 위해 device_id 주입
        for data in telemetry_list:
            data['device_id'] = device_id
            
        return telemetry_crud_command.bulk_upsert(db, obj_in_list=telemetry_list)

telemetry_command_service = TelemetryCommandService()