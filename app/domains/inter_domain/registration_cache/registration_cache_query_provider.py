from typing import Optional

from app.domains.services.registration_cache.schemas.registration_cache_query import RegistrationDataResponse
from app.domains.services.registration_cache.services.registration_cache_query_service import registration_cache_query_service

class RegistrationCacheQueryProvider:
    def get_registration_data(self, *, code: str) -> Optional[RegistrationDataResponse]:
        return registration_cache_query_service.get_registration_data(code=code)

registration_cache_query_provider = RegistrationCacheQueryProvider()
