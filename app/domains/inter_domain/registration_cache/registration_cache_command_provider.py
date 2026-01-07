from app.domains.services.registration_cache.schemas.registration_cache_command import CacheRegistrationData
from app.domains.services.registration_cache.services.registration_cache_command_service import registration_cache_command_service

class RegistrationCacheCommandProvider:
    def cache_registration_data(self, *, data: CacheRegistrationData, code: str, ttl_seconds: int) -> bool:
        return registration_cache_command_service.cache_registration_data(
            data=data, code=code, ttl_seconds=ttl_seconds
        )

    def delete_registration_data(self, *, code: str) -> bool:
        return registration_cache_command_service.delete_registration_data(code=code)

registration_cache_command_provider = RegistrationCacheCommandProvider()
