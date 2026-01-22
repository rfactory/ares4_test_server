import logging
import time
import secrets
import hashlib
import base64
import json
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

from jose import jwt, JWTError, jwk as jose_jwk
from passlib.context import CryptContext
from fastapi import HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.domains.services.token_management.schemas.token_management_query import TokenPayload
from app.core.redis_client import get_redis_client

# 로거 설정
logger = logging.getLogger(__name__)

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 스킴 설정 (Swagger UI 등을 위해 유지하되, 실제 추출은 커스텀 함수 사용)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login/access-token", auto_error=False)

# DPoP 관련 상수
DPOP_NONCE_EXPIRATION_SECONDS = 300  # 5분
DPOP_PROOF_IAT_MAX_AGE_SECONDS = 60  # DPoP 증명 iat 유효 시간 (60초)

# --- 토큰 추출 및 검증 관련 함수 ---

async def extract_token_from_request(request: Request) -> str:
    """
    Authorization 헤더에서 토큰을 추출합니다.
    DPoP 및 Bearer 스킴을 모두 지원합니다.
    """
    authorization: str = request.headers.get("Authorization")
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "DPoP", "DPoP-Nonce": generate_dpop_nonce()},
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() not in ["dpop", "bearer"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Unsupported authentication scheme: {scheme}. Use DPoP or Bearer.",
                headers={"WWW-Authenticate": "DPoP", "DPoP-Nonce": generate_dpop_nonce()},
            )
        return token
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format",
            headers={"WWW-Authenticate": "DPoP", "DPoP-Nonce": generate_dpop_nonce()},
        )

def generate_dpop_nonce() -> str:
    """새로운 DPoP Nonce를 생성하고 Redis에 저장합니다."""
    nonce = secrets.token_urlsafe(32)
    redis_client = get_redis_client()
    redis_client.set(f"dpop_nonce:{nonce}", 1, ex=DPOP_NONCE_EXPIRATION_SECONDS)
    return nonce

def verify_dpop_nonce(nonce: str) -> bool:
    """DPoP Nonce의 유효성을 검사하고, 사용되었으면 삭제(일회용)합니다."""
    redis_client = get_redis_client()
    redis_key = f"dpop_nonce:{nonce}"
    was_present = redis_client.delete(redis_key)
    return was_present == 1

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- 토큰 생성 관련 함수 ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None, dpop_jkt: Optional[str] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # DPoP jkt (JWK Thumbprint) 바인딩 클레임 추가
    if dpop_jkt:
        to_encode["cnf"] = {"jkt": dpop_jkt}

    secret_keys = settings.JWT_SECRET_KEYS.split(',')
    encoded_jwt = jwt.encode(to_encode, secret_keys[0], algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "jti": secrets.token_urlsafe(16)})
    
    secret_keys = settings.JWT_SECRET_KEYS.split(',')
    encoded_jwt = jwt.encode(to_encode, secret_keys[0], algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

# --- 검증 로직 관련 함수 ---

def decode_access_token(token: str, dpop_jkt: Optional[str] = None) -> Dict[str, Any]:
    """Access Token을 디코딩하여 전체 payload를 반환합니다."""
    payload = None
    secret_keys = settings.JWT_SECRET_KEYS.split(',')
    
    for key in secret_keys:
        try:
            payload = jwt.decode(token, key, algorithms=[settings.JWT_ALGORITHM])
            break
        except JWTError:
            continue
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials (decode)",
            headers={"WWW-Authenticate": "DPoP", "DPoP-Nonce": generate_dpop_nonce()},
        )

    # DPoP 바인딩 검증
    if dpop_jkt:
        cnf = payload.get("cnf")
        if not cnf or "jkt" not in cnf or cnf["jkt"] != dpop_jkt:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="DPoP token binding failed",
                headers={"WWW-Authenticate": "DPoP", "DPoP-Nonce": generate_dpop_nonce()}
            )
    return payload

def verify_access_token(token: str, dpop_jkt: Optional[str] = None) -> TokenPayload:
    """Access Token의 유효성을 검증하고 DPoP 바인딩(jkt)을 확인합니다."""
    payload = decode_access_token(token, dpop_jkt=dpop_jkt)
    try:
        user_id = int(payload.get("sub"))
        return TokenPayload(id=user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

async def verify_dpop_proof(request: Request, access_token: Optional[str] = None) -> str:
    """
    DPoP Proof JWT를 검증하고, 공개키 지문(jkt)을 반환합니다.
    HTU 검증 시 경로(path) 기반 비교를 수행하여 환경 호환성을 높였습니다.
    """
    dpop_header = request.headers.get("DPoP")
    
    if not dpop_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail={"error": "use_dpop_nonce", "message": "DPoP header missing"}, 
            headers={"DPoP-Nonce": generate_dpop_nonce()}
        )

    try:
        # 1. 헤더에서 공개키(JWK) 추출
        dpop_header_data = jwt.get_unverified_header(dpop_header)
        public_jwk = dpop_header_data.get("jwk")
        if not public_jwk:
            raise ValueError("JWK missing in DPoP header")
            
        public_key = jose_jwk.construct(public_jwk)

        # 2. 서명 및 기본 페이로드 검증
        dpop_payload = jwt.decode(
            dpop_header,
            public_key,
            algorithms=[dpop_header_data.get("alg", "ES256")]
        )
        
        # 3. JTI 재사용 검증 (Replay Attack 방지)
        jti = dpop_payload.get("jti")
        if not jti: raise ValueError("jti missing")
        
        redis_client = get_redis_client()
        redis_key = f"dpop_jti:{jti}"
        if redis_client.exists(redis_key):
            raise HTTPException(status_code=401, detail={"error": "use_dpop_nonce", "message": "DPoP proof re-used"})
        redis_client.set(redis_key, 1, ex=120)

        # 4. Nonce 검증
        nonce = dpop_payload.get("nonce")
        if not nonce or not verify_dpop_nonce(nonce):
            raise ValueError("Invalid or missing Nonce")

        # 5. iat (발급 시간) 검증
        iat = dpop_payload.get("iat")
        if not iat or abs(time.time() - iat) > DPOP_PROOF_IAT_MAX_AGE_SECONDS:
            raise ValueError("DPoP proof expired (iat)")

        # 6. htm (Method) 검증
        if dpop_payload.get("htm") != request.method:
            raise ValueError("htm mismatch")

        # 7. [핵심] htu (URL Path) 검증
        # 도메인/포트 불일치 대응을 위해 경로(path)만 비교
        expected_path = request.url.path
        actual_htu = dpop_payload.get("htu", "")
        actual_path = urlparse(actual_htu).path if actual_htu else ""
        
        if actual_path != expected_path:

            raise ValueError("htu path mismatch")

        # 8. ath (Access Token Hash) 검증
        if access_token:
            hashed = hashlib.sha256(access_token.encode('utf-8')).digest()
            expected_ath = base64.urlsafe_b64encode(hashed).rstrip(b'=').decode('utf-8')
            if dpop_payload.get("ath") != expected_ath:
                raise ValueError("ath mismatch")

        # 9. JKT (JWK Thumbprint) 계산 (RFC 7638)
        required_fields = sorted(["crv", "kty", "x", "y"])
        thumbprint_fields = {k: public_jwk[k] for k in required_fields if k in public_jwk}
        canonical_json = json.dumps(thumbprint_fields, sort_keys=True, separators=(',', ':')).encode('utf-8')
        calculated_jkt = base64.urlsafe_b64encode(hashlib.sha256(canonical_json).digest()).rstrip(b'=').decode('utf-8')
        
        return calculated_jkt

    except (JWTError, ValueError, KeyError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail={"error": "use_dpop_nonce", "message": f"Invalid DPoP proof: {str(e)}"},
            headers={"DPoP-Nonce": generate_dpop_nonce()}
        )

# --- HMAC 및 기타 보안 유틸리티 (기존 유지) ---

def generate_shared_secret(length: int = 32) -> str:
    return secrets.token_urlsafe(length)

def generate_hmac(payload_data: dict, shared_secret: str) -> Optional[str]:
    if 'timestamp' not in payload_data or not shared_secret:
        return None
    canonical_string = f"{payload_data['timestamp']}|{json.dumps(payload_data, sort_keys=True)}"
    signature = hmac.new(shared_secret.encode('utf-8'), canonical_string.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(signature).decode('utf-8')

def verify_hmac(payload_data: dict, shared_secret: str, received_hmac: str) -> bool:
    if not received_hmac or not shared_secret:
        return False
    payload_copy = payload_data.copy()
    if 'hmac' in payload_copy:
        del payload_copy['hmac']
    expected_hmac = generate_hmac(payload_copy, shared_secret)
    return hmac.compare_digest(expected_hmac, received_hmac) if expected_hmac else False