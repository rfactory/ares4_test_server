from typing import List
from app.domains.services.abac.services.abac_query_service import abac_query_service
from app.domains.services.abac.schemas.abac_query import AbacVariableResponse

class AbacQueryProvider:
    def get_abac_variables(self) -> List[AbacVariableResponse]:
        """ABAC 변수 목록을 서비스에서 가져와 응답 스키마로 변환합니다."""
        variables = abac_query_service.get_abac_variables()
        return [AbacVariableResponse(**var) for var in variables]

abac_query_provider = AbacQueryProvider()
