import logging
from typing import Tuple, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.domains.inter_domain.device_management.schemas.device_query import DeviceRead

logger = logging.getLogger(__name__)

class DeviceOwnershipValidator:
    def validate(
        self, 
        *, 
        user_id: int, 
        user_org_ids: List[int], # 유저가 속한 조직 ID 리스트 (밖에서 조회해서 줌)
        device: "DeviceRead", 
        access: str
    ) -> Tuple[bool, Optional[str]]:
        """
        주어진 정보(User, Org, Device)를 바탕으로 권한 여부만 판단합니다. (DB 조회 없음)
        """
        
        # 1. 조직 권한 확인
        if hasattr(device, 'organization_devices'):
            for org_dev in device.organization_devices:
                # 사용자가 이 장치가 속한 조직의 멤버인지 확인
                if org_dev.organization_id in user_org_ids and org_dev.is_active:
                    if org_dev.relationship_type in ['OWNER', 'OPERATOR']:
                        return True, None
                    if org_dev.relationship_type == 'VIEWER' and access == 'subscribe':
                        return True, None

        # 2. 개인 권한 확인
        if hasattr(device, 'users'):
            for user_dev in device.users:
                if user_dev.user_id == user_id and user_dev.is_active:
                    if user_dev.role == 'owner':
                        return True, None
                    if user_dev.role == 'viewer' and access == 'subscribe':
                        return True, None

        return False, "ACL_DENIED: No valid ownership found."

device_ownership_validator = DeviceOwnershipValidator()