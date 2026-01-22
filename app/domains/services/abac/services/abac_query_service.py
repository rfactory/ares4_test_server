from typing import List, Dict, Any

class AbacQueryService:
    def get_abac_variables(self) -> List[Dict[str, Any]]:
        """ABAC 필터 조건에서 사용할 수 있는 동적 변수 목록을 반환합니다."""
        # 현재는 하드코딩된 목록을 반환합니다. 추후 DB나 다른 설정에서 관리할 수 있습니다.
        return [
            {
                "name": "{{current_user.id}}",
                "description": "The ID of the currently logged-in user."
            },
            {
                "name": "{{current_user.organization_id}}",
                "description": "The organization ID of the currently logged-in user's active context."
            },
        ]

abac_query_service = AbacQueryService()
