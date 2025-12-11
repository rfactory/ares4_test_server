# file: server2/app/domains/inter_domain/device_management/schemas/device_command.py
"""
이 파일은 device_management 도메인의 'command' 관련 스키마를 다른 도메인에 안전하게 노출(re-export)합니다.
"""
from app.domains.services.device_management.schemas.device_command import DeviceBase, DeviceCreate, DeviceUpdate
