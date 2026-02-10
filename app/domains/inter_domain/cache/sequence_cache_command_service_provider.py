from app.domains.services.cache.services.sequence_cache_command_service import sequence_cache_command_service
from typing import Optional


class SequenceCacheProvider:
    """[Ares Aegis] 타 도메인에서 캐시 서비스를 이용하기 위한 공식 통로"""
    
    def get_last_seq(self, device_id: int, instance_name: str) -> Optional[int]:
        return sequence_cache_command_service.get_last_sequence(device_id, instance_name)

    def set_last_seq(self, device_id: int, instance_name: str, seq: int):
        sequence_cache_command_service.update_last_sequence(device_id, instance_name, seq)

# 싱글톤 인스턴스
sequence_cache_command_provider = SequenceCacheProvider()