# file: server2/app/domains/inter_domain/user_identity/schemas/models.py
"""
이 파일은 user_identity 도메인과 관련된 SQLAlchemy 모델을 다른 도메인에 안전하게 노출(re-export)합니다.
"""
from app.models.objects.user import User
