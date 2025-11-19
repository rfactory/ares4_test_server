from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

from app.dependencies import get_db
from app.domains.accounts.schemas import Token
from app.domains.accounts.crud import user_crud
from app.core.security import verify_password, create_access_token
from app.core.utils import generate_random_code, send_email
from app.models.objects.user import User as DBUser
from app.core.config import settings

router = APIRouter()

class TwoFactorRequest(BaseModel):
    username: str
    code: str

def _issue_access_token(user: DBUser) -> Token:
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@router.post("/token", summary="Login with username and password")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    Handles the first step of authentication (username and password).
    If 2FA is enabled, it sends a code to the user's email.
    Otherwise, it returns an access token directly.
    """
    user = user_crud.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.is_two_factor_enabled:
        # 1. Generate and save 2FA code
        code = generate_random_code()
        user.email_verification_token = code
        user.email_verification_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        db.commit()

        # 2. Send code via email
        await send_email(
            subject="Your 2FA Code",
            recipient=user.email,
            body=f"Your two-factor authentication code is: <strong>{code}</strong>"
        )
        
        return {"message": "2FA required. Please check your email for the code."}

    # If 2FA is not enabled, issue token directly
    return _issue_access_token(user)


@router.post("/token/2fa", response_model=Token, summary="Verify 2FA and get access token")
async def verify_two_factor_code(
    two_factor_data: TwoFactorRequest, db: Session = Depends(get_db)
):
    """
    Handles the second step of authentication (2FA code verification).
    """
    user = user_crud.get_user_by_username(db, username=two_factor_data.username)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if (
        not user.email_verification_token
        or user.email_verification_token != two_factor_data.code
        or user.email_verification_token_expires_at < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired 2FA code",
        )

    # Clear the 2FA code after successful verification
    user.email_verification_token = None
    user.email_verification_token_expires_at = None
    db.commit()

    # Issue token
    return _issue_access_token(user)