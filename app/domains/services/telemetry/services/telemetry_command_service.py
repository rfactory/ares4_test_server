# C:\vscode project files\Ares4\server2\app\domains\services\telemetry\services\telemetry_command_service.py

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Union, TYPE_CHECKING, cast
from datetime import datetime, timezone

from app.models.events_logs.telemetry_data import TelemetryData
from ..crud.telemetry_command_crud import telemetry_crud_command
from ..schemas.telemetry_command import TelemetryCommandDataCreate

if TYPE_CHECKING:
    from app.models.objects.system_unit import SystemUnit
    from app.models.objects.device import Device

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
    
    def process_cluster_batch_ingestion(self, db: Session, *, system_unit: "SystemUnit", payload: Dict[str, Any]):
        """
        [Laborer] 클러스터 페이로드를 노드별로 분해하고 낱개 데이터로 변환하여 저장합니다.
        """
        nodes: List[Dict[str, Any]] = payload.get('nodes', [])
        global_snapshot_id = payload.get('snapshot_id', 'cluster_sync')
        
        devices = cast(List["Device"], system_unit.devices)
        member_map = {str(d.current_uuid): d for d in devices}
        
        telemetry_create_list: List[TelemetryCommandDataCreate] = []

        for node in nodes:
            node_uuid = node.get('device_uuid')
            device = member_map.get(str(node_uuid))
            
            if not device:
                continue

            instance_name = str(node.get('instance_name', 'default'))
            metrics: List[Dict[str, Any]] = node.get('metrics', [])

            for m in metrics:
                captured_at = self._parse_timestamp(m.get('timestamp'))
                avg_val = float(m.get('avg_value', m.get('avg', 0.0)))

                telemetry_create_list.append(
                    TelemetryCommandDataCreate(
                        device_id=device.id,
                        system_unit_id=system_unit.id,
                        snapshot_id=global_snapshot_id,
                        captured_at=captured_at,
                        component_name=instance_name,
                        metric_name=str(m.get('metric_name')),
                        avg_value=avg_val,
                        min_value=float(m.get('min_value', m.get('min', avg_val))),
                        max_value=float(m.get('max_value', m.get('max', avg_val))),
                        std_dev=float(m.get('std_dev', 0.0)),
                        slope=float(m.get('slope', 0.0)),
                        sample_count=int(m.get('sample_count', m.get('count', 1))),
                        extra_stats=m.get('extra')
                    )
                )

        if telemetry_create_list:
            return self.create_multiple_telemetry(db, obj_in_list=telemetry_create_list)
        
    def _parse_timestamp(self, ts: Union[str, int, float, None]) -> datetime:
        """타임스탬프 유연 파싱 헬퍼"""
        if not ts: return datetime.now(timezone.utc)
        try:
            if isinstance(ts, (int, float)):
                if ts > 10000000000: ts /= 1000.0
                return datetime.fromtimestamp(ts, timezone.utc)
            return datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
        except:
            return datetime.now(timezone.utc)
        
telemetry_command_service = TelemetryCommandService()