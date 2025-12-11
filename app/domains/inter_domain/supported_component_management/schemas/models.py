# file: server2/app/domains/inter_domain/supported_component_management/schemas/models.py
"""
이 파일은 supported_component_management 도메인의 SQLAlchemy 모델 및 Pydantic 스키마를
다른 도메인에 안전하게 노출(re-export)합니다.
"""
from app.domains.services.supported_component_management.schemas.supported_component_query import SupportedComponentRead
