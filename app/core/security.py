from datetime import datetime, timedelta, timezone
from typing import Optional
import hmac
import hashlib
import base64
import json
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import secrets # ADDED

from app.core.config import settings
from app.domains.inter_domain.token.schemas.token_command import TokenData # Use the new inter-domain path

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES) # Corrected attribute name
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM) # Corrected attribute names
    return encoded_jwt

def verify_access_token(token: str) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]) # Corrected attribute names
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    return token_data

def generate_shared_secret(length: int = 32) -> str: # ADDED
    """Generates a secure, URL-safe random string for shared secrets."""
    return secrets.token_urlsafe(length)

# --- HMAC Signature (Ported from server project) ---

def generate_hmac(payload_data: dict, shared_secret: str) -> str | None:
    """
    Generates an HMAC-SHA256 signature for a given payload dictionary.
    The canonical string format is: 'timestamp|sorted_json_payload'
    """
    if 'timestamp' not in payload_data or not shared_secret:
        return None

    # In server2, the payload might not be nested under 'value'. Adjust if necessary.
    canonical_string = f"{payload_data['timestamp']}|{json.dumps(payload_data, sort_keys=True)}"
    signature = hmac.new(shared_secret.encode('utf-8'), canonical_string.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(signature).decode('utf-8')

def verify_hmac(payload_data: dict, shared_secret: str, received_hmac: str) -> bool:
    """
    Verifies the received HMAC signature by regenerating it on the server side.
    Returns True if the signatures match, False otherwise.
    """
    if not received_hmac or not shared_secret:
        return False

    # The received payload will contain the hmac, which should not be part of the signature calculation.
    payload_copy = payload_data.copy()
    if 'hmac' in payload_copy:
        del payload_copy['hmac']

    expected_hmac = generate_hmac(payload_copy, shared_secret)
    if expected_hmac is None:
        return False

    return hmac.compare_digest(expected_hmac, received_hmac)

