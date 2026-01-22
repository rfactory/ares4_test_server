import logging
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import inspect
from sqlalchemy.sql.type_api import TypeEngine

from app.dependencies import get_db, PermissionChecker
from app.domains.inter_domain.common.schemas.common_query import ManageableResourceResponse, ResourceColumn
from app.core.abac_managed_resources import MANAGEABLE_MODELS

router = APIRouter()
logger = logging.getLogger(__name__)

def _map_sql_type_to_string(sql_type: TypeEngine) -> str:
    """SQLAlchemy 타입을 간단한 문자열로 매핑합니다."""
    py_type = sql_type.python_type
    if issubclass(py_type, (int, float)):
        return "number"
    if issubclass(py_type, bool):
        return "boolean"
    if issubclass(py_type, str):
        return "string"
    return "unknown"


@router.get(
    "/manageable-resources",
    response_model=List[ManageableResourceResponse],
    dependencies=[Depends(PermissionChecker("permission:read"))]
)
async def get_manageable_resources() -> List[ManageableResourceResponse]:
    """
    ABAC 규칙에서 필터링 대상으로 지정할 수 있는 리소스(테이블) 및 컬럼 메타데이터를 동적으로 조회합니다.
    """
    logger.info("Fetching manageable resources...")
    response = []
    for resource_name, config in MANAGEABLE_MODELS.items():
        model_class = config["model"]
        exclude_columns = config.get("exclude_columns", [])
        try:
            logger.info(f"Inspecting model: {model_class.__name__}")
            inspector = inspect(model_class)
            
            filtered_columns = []
            for c in inspector.c:
                if c.name not in exclude_columns:
                    filtered_columns.append(
                        ResourceColumn(
                            name=c.name,
                            type=_map_sql_type_to_string(c.type)
                        )
                    )
            logger.info(f"Found columns for {model_class.__name__}: {[c.name for c in filtered_columns]}")

            response.append(
                ManageableResourceResponse(resource_name=resource_name, columns=filtered_columns)
            )
        except Exception as e:
            logger.error(f"Failed to inspect model {model_class.__name__}: {e}", exc_info=True)
            continue
    logger.info(f"Returning {len(response)} manageable resources.")
    return response

