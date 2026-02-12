from typing import List, Tuple
from app.models.objects.system_unit import SystemUnit
from app.domains.action_authorization.validators.cluster_authority.cluster_membership_validator import ClusterMembershipValidator

class ClusterMembershipValidatorProvider:
    """[Inter-Domain] 클러스터 멤버십 소속 검증 공급자"""
    def __init__(self):
        self._validator = ClusterMembershipValidator()

    def validate_nodes(self, node_uuids: List[str], unit: SystemUnit) -> Tuple[bool, List[str]]:
        return self._validator.validate_nodes(node_uuids, unit)

cluster_membership_validator_provider = ClusterMembershipValidatorProvider()