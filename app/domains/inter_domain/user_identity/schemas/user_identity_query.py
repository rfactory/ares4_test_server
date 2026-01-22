# file: server2/app/domains/inter_domain/user_identity/schemas/user_identity_query.py
"""
이 파일은 user_identity 도메인의 'query' 관련 Pydantic 스키마를 다른 도메인에 안전하게 노출(re-export)합니다.
"""
from app.domains.services.user_identity.schemas.user_identity_query import UserBase, UserInDBBase, User, UserWithToken, MemberResponse
