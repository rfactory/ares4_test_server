from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone

from app.domains.inter_domain.user_identity.providers import user_identity_providers
from app.core.security import verify_password, create_access_token
from app.core.utils import generate_random_code, send_email
from app.core.config import settings
from app.core.exceptions import PermissionDeniedError, NotFoundError
from app.domains.inter_domain.audit.providers import audit_providers


class AuthService:
    async def login(self, db: Session, *, form_data: OAuth2PasswordRequestForm) -> dict:
        user = user_identity_providers.get_user_by_username(db, username=form_data.username)
        
        if not user or not verify_password(form_data.password, user.password_hash):
            if user:
                audit_providers.log(
                    db=db,
                    event_type="USER_LOGIN_FAILED",
                    description=f"Failed login attempt for user: {user.username}",
                    actor_user=user, 
                    target_user=user,
                    details={"username_attempted": form_data.username}
                )
            raise PermissionDeniedError("Incorrect username or password")

        audit_providers.log(
            db=db,
            event_type="USER_LOGIN_SUCCESS",
            description=f"User '{user.username}' logged in successfully.",
            actor_user=user,
            target_user=user
        )

        if user.is_two_factor_enabled:
            code = generate_random_code()
            user.email_verification_token = code
            user.email_verification_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES)
            db.commit()

            await send_email(
                subject="Your 2FA Code",
                recipient=user.email,
                body=f"Your two-factor authentication code is: <strong>{code}</strong>"
            )
            return {"message": "2FA required. Please check your email for the code."}
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    async def verify_2fa(self, db: Session, *, username: str, code: str) -> dict:
        user = user_identity_providers.get_user_by_username(db, username=username)
        if not user:
            raise NotFoundError(resource_name="User", resource_id=username)

        if (
            not user.email_verification_token
            or user.email_verification_token != code
            or not user.email_verification_token_expires_at
            or user.email_verification_token_expires_at < datetime.now(timezone.utc)
        ):
            raise PermissionDeniedError("Invalid or expired 2FA code")

        user.email_verification_token = None
        user.email_verification_token_expires_at = None
        db.commit()

        audit_providers.log(
            db=db,
            event_type="USER_2FA_VERIFIED",
            description=f"User '{user.username}' successfully verified 2FA.",
            actor_user=user,
            target_user=user
        )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

auth_service = AuthService()
