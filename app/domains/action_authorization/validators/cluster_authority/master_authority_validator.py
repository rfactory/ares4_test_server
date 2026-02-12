from typing import Tuple, Optional
from app.models.objects.device import Device
from app.models.objects.system_unit import SystemUnit

class MasterAuthorityValidator:
    """기기가 시스템 유닛(클러스터)의 마스터 권한을 가졌는지 검증합니다."""
    def validate(self, device: Device, unit: SystemUnit) -> Tuple[bool, Optional[str]]:
        if unit.master_device_id != device.id:
            return False, f"Master Authority Denied: Device {device.id} is not the master of Unit {unit.id}"
        return True, None