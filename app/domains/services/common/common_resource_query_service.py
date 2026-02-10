import logging
from typing import List
from sqlalchemy import inspect
from app.domains.inter_domain.common.schemas.common_query import ManageableResourceResponse, ResourceColumn
from app.core.abac_managed_resources import MANAGEABLE_MODELS

logger = logging.getLogger(__name__)

class ResourceMetadataService:
    """[Service] 시스템 모델을 분석하여 메타데이터를 추출하는 실제 구현체"""

    def _map_sql_type_to_string(self, sql_type) -> str:
        """SQLAlchemy 타입을 프론트엔드용 문자열로 변환"""
        try:
            py_type = sql_type.python_type
            if issubclass(py_type, (int, float)): return "number"
            if issubclass(py_type, bool): return "boolean"
            if issubclass(py_type, str): return "string"
        except Exception:
            pass
        return "unknown"

    def get_manageable_resources_metadata(self) -> List[ManageableResourceResponse]:
        """등록된 관리 대상 모델들의 컬럼 정보를 동적으로 추출"""
        response = []
        for resource_name, config in MANAGEABLE_MODELS.items():
            model_class = config["model"]
            exclude_columns = config.get("exclude_columns", [])
            
            try:
                inspector = inspect(model_class)
                filtered_columns = [
                    ResourceColumn(
                        name=c.name, 
                        type=self._map_sql_type_to_string(c.type)
                    )
                    for c in inspector.c if c.name not in exclude_columns
                ]
                
                response.append(ManageableResourceResponse(
                    resource_name=resource_name, 
                    columns=filtered_columns
                ))
            except Exception as e:
                logger.error(f"Failed to inspect model {model_class.__name__}: {e}")
                continue
        return response

resource_metadata_service = ResourceMetadataService()