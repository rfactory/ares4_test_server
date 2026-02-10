import logging
from typing import Optional
from app.core.redis_client import get_redis_client

redis_client = get_redis_client()

logger = logging.getLogger(__name__)

class SequenceCacheService:
    """[Ares Aegis] Redis를 활용한 시퀀스 번호 관리 실무 로직"""

    def get_last_sequence(self, device_id: int, instance_name: str) -> Optional[int]:
        key = f"last_seq:{device_id}:{instance_name}"
        try:
            val = redis_client.get(key)
            return int(val) if val else None
        except (ValueError, TypeError, Exception) as e:
            logger.error(f"Failed to fetch sequence from Redis: {e}")
            return None

    def update_last_sequence(self, device_id: int, instance_name: str, seq: int):
        key = f"last_seq:{device_id}:{instance_name}"
        try:
            # 시퀀스 보존 기간은 기기 정책에 따라 설정 (예: 7일)
            redis_client.set(key, str(seq), ex=604800)
        except Exception as e:
            logger.error(f"Failed to update sequence in Redis: {e}")

sequence_cache_command_service = SequenceCacheService()