import redis
from app.core.config import get_settings

def get_redis_client():
    settings = get_settings()
    return redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
