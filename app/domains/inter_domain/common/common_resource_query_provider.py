from typing import List
from app.domains.inter_domain.common.schemas.common_query import ManageableResourceResponse
# 다니엘님이 이미 만드신 서비스를 임포트합니다.
from app.domains.services.common.common_resource_query_service import resource_metadata_service

class CommonResourceQueryProvider:
    """
    [Inter-Domain] 이미 존재하는 ResourceMetadataService를 
    외부 도메인(API 등)에 연결해주는 공식 조회 창구입니다.
    """

    def fetch_manageable_resources(self) -> List[ManageableResourceResponse]:
        # 이미 잘 짜여진 서비스의 메서드를 호출만 합니다.
        return resource_metadata_service.get_manageable_resources_metadata()

# 이름에 'query_provider'를 넣어 다른 도메인들과 형제처럼 맞춥니다.
common_resource_query_provider = CommonResourceQueryProvider()