# file: server2/app/domains/inter_domain/token/schemas/token_command.py
"""
이 파일은 token 도메인의 'command' 관련 스키마를 다른 도메인에 안전하게 노출(re-export)합니다.
"""
from app.domains.services.token.schemas.token_command import Token, TokenData
