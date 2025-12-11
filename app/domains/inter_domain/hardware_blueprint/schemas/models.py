# file: server2/app/domains/inter_domain/hardware_blueprint/schemas/models.py
"""
이 파일은 hardware_blueprint 도메인의 SQLAlchemy 모델 및 Pydantic 스키마를
다른 도메인에 안전하게 노출(re-export)합니다.
"""
from app.domains.services.hardware_blueprint.schemas.hardware_blueprint_query import HardwareBlueprintRead
