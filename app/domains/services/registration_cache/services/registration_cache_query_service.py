import redis
import json
from typing import Optional

from app.core.config import settings
from ..schemas.registration_cache_query import RegistrationDataResponse

class RegistrationCacheQueryService:
    """
    가입 정보 임시 저장(Redis)에 대한 Query 작업을 담당합니다.
    """
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB, decode_responses=True
        )

    def get_registration_data(self, *, code: str) -> Optional[RegistrationDataResponse]:
        """
        인증 코드를 키로 하여 Redis에서 임시 가입 데이터를 조회합니다.
        """
        redis_key = f"registration:{code}"
        data_str = self.redis_client.get(redis_key)
        if not data_str:
            return None
        
        data_dict = json.loads(data_str)
        return RegistrationDataResponse(**data_dict)

registration_cache_query_service = RegistrationCacheQueryService()
