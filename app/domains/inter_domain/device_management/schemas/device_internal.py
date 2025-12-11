# inter_domain/device_management/schemas/device_internal.py
"""
내부용 장치 스키마를 다른 도메인에 안전하게 노출(re-export)합니다.
"""
from app.domains.services.device_management.schemas.device_internal import DeviceWithSecret
