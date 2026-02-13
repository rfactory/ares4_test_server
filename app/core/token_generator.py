import secrets
import string
from enum import Enum
from typing import Optional

class TokenType(str, Enum):
    ALPHANUMERIC = "alphanumeric"   # 대소문자 + 숫자 (기본)
    NUMERIC = "numeric"             # 숫자만 (PIN 코드 등)
    HEX = "hex"                     # 16진수 (API Key, Device ID 등)
    URL_SAFE = "url_safe"           # URL에 넣어도 되는 문자열 (Base64 변형)

class TokenGenerator:
    """
    [Utility] 시스템 전역에서 사용되는 토큰 생성기
    요청받은 조건(길이, 타입, 접두사)에 맞춰 안전한 난수를 생성합니다.
    """

    @staticmethod
    def generate(
        length: int = 32, 
        type: TokenType = TokenType.ALPHANUMERIC, 
        prefix: Optional[str] = None
    ) -> str:
        """
        조건에 맞는 토큰을 생성하여 반환합니다.
        
        Args:
            length (int): 생성할 토큰의 길이 (접두사 제외)
            type (TokenType): 토큰의 문자셋 타입
            prefix (str, optional): 토큰 앞에 붙일 고정 문자열 (예: 'sk_live_')
        """
        if length < 1:
            raise ValueError("Token length must be at least 1.")

        token_body = ""

        if type == TokenType.NUMERIC:
            # 6자리 인증번호 등 (0-9)
            chars = string.digits
            token_body = ''.join(secrets.choice(chars) for _ in range(length))
        
        elif type == TokenType.HEX:
            # 16진수 (바이트 단위이므로 length는 바이트 수로 해석하거나, 문자 길이로 맞춤)
            # 여기서는 문자 길이를 맞추기 위해 length // 2 바이트를 생성
            token_body = secrets.token_hex(length // 2 + 1)[:length]
            
        elif type == TokenType.URL_SAFE:
            # URL Safe Base64 (length는 바이트 수 기준이므로 약간 다를 수 있음 -> 문자 길이로 조정)
            token_body = secrets.token_urlsafe(length)[:length]
            
        else: # ALPHANUMERIC (Default)
            # 대소문자 + 숫자 (가장 일반적인 랜덤 스트링)
            chars = string.ascii_letters + string.digits
            token_body = ''.join(secrets.choice(chars) for _ in range(length))

        # 접두사가 있으면 붙여서 반환
        return f"{prefix}{token_body}" if prefix else token_body

# 싱글톤 인스턴스 (필요 시 DI로 주입 가능)
token_generator = TokenGenerator()