import redis
import json

from app.core.config import settings
from ..schemas.registration_cache_command import CacheRegistrationData

class RegistrationCacheCommandService:
    """
    가입 정보 임시 저장(Redis)에 대한 Command 작업을 담당합니다.
    """
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB
        )

    def cache_registration_data(self, *, data: CacheRegistrationData, code: str, ttl_seconds: int):
        """
        가입 데이터를 코드를 키로 하여 Redis에 저장하고 만료시간(TTL)을 설정합니다.
        """
        redis_key = f"registration:{code}"
        self.redis_client.set(redis_key, data.model_dump_json(), ex=ttl_seconds)
        return True

    def delete_registration_data(self, *, code: str):
        """
        Redis에서 가입 데이터를 삭제합니다.
        """
        redis_key = f"registration:{code}"
        self.redis_client.delete(redis_key)
        return True

registration_cache_command_service = RegistrationCacheCommandService()
