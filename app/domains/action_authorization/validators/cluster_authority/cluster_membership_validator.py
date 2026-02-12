from typing import List, Set, Tuple, Optional
from app.models.objects.system_unit import SystemUnit

class ClusterMembershipValidator:
    """페이로드의 노드들이 유닛의 정당한 멤버인지 검증합니다."""
    def validate_nodes(self, node_uuids: List[str], unit: SystemUnit) -> Tuple[bool, List[str]]:
        # 유닛에 등록된 멤버 UUID 세트 생성
        allowed_uuids = {str(d.current_uuid) for d in unit.devices}
        
        # 소속되지 않은 외부인(Intruder) 색출
        invalid_nodes = [uuid for uuid in node_uuids if uuid not in allowed_uuids]
        
        if invalid_nodes:
            return False, invalid_nodes
        return True, []