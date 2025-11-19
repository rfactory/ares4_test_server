import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.domains.accounts.crud import user_crud
from app.domains.accounts.schemas import UserCreate
from app.core.security import get_password_hash

@pytest.mark.anyio
async def test_login_for_access_token(client: AsyncClient, db_session: Session):
    """
    Test successful login and token generation for a user without 2FA.
    """
    # Create a user directly in the DB for this test
    user_data = {
        "username": "loginuser",
        "email": "login@example.com",
        "password": "loginpassword"
    }
    hashed_password = get_password_hash(user_data["password"])
    user_in_db = user_crud.create_user(db_session, UserCreate(
        username=user_data["username"],
        email=user_data["email"],
        password=user_data["password"] # crud handles hashing
    ))
    
    response = await client.post(
        "/api/v1/users/token",
        data={"username": user_data["username"], "password": user_data["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.anyio
async def test_login_for_access_token_invalid_credentials(client: AsyncClient):
    """
    Test login with invalid username or password.
    """
    response = await client.post(
        "/api/v1/users/token",
        data={"username": "nonexistent", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

@pytest.mark.anyio
async def test_login_for_access_token_2fa_required(client: AsyncClient, db_session: Session, mocker):
    """
    Test login for a user with 2FA enabled, expecting a 2FA code request.
    """
    # Create a user with 2FA enabled
    user_data = {
        "username": "2fauser",
        "email": "2fa@example.com",
        "password": "2fapassword"
    }
    user_in_db = user_crud.create_user(db_session, UserCreate(
        username=user_data["username"],
        email=user_data["email"],
        password=user_data["password"],
        is_two_factor_enabled=True # 직접 True로 설정
    ))

    # Mock send_email function
    mock_send_email = mocker.patch("app.domains.accounts.endpoints_auth.send_email", new_callable=AsyncMock)

    response = await client.post(
        "/api/v1/users/token",
        data={"username": user_data["username"], "password": user_data["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "2FA required. Please check your email for the code."
    
    # Verify email was sent
    mock_send_email.assert_called_once()
    assert "Your two-factor authentication code is:" in mock_send_email.call_args[1]["body"]
    
    # Verify 2FA token and expiry are set in DB
    updated_user = user_crud.get_user_by_username(db_session, username=user_data["username"])
    assert updated_user.email_verification_token is not None
    assert updated_user.email_verification_token_expires_at is not None
    assert updated_user.email_verification_token_expires_at > datetime.now(timezone.utc)

@pytest.mark.anyio
async def test_verify_two_factor_code_success(client: AsyncClient, db_session: Session):
    """
    Test successful 2FA code verification and token generation.
    """
    # Create a user with 2FA enabled and a verification token
    user_data = {
        "username": "verify2fauser",
        "email": "verify2fa@example.com",
        "password": "verify2fapassword"
    }
    user_in_db = user_crud.create_user(db_session, UserCreate(
        username=user_data["username"],
        email=user_data["email"],
        password=user_data["password"]
    ))
    user_in_db.is_two_factor_enabled = True
    user_in_db.email_verification_token = "123456"
    user_in_db.email_verification_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    db_session.add(user_in_db)
    db_session.commit()
    db_session.refresh(user_in_db)

    response = await client.post(
        "/api/v1/users/token/2fa",
        json={"username": user_data["username"], "code": "123456"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Verify 2FA token and expiry are cleared
    updated_user = user_crud.get_user_by_username(db_session, username=user_data["username"])
    assert updated_user.email_verification_token is None
    assert updated_user.email_verification_token_expires_at is None

@pytest.mark.anyio
async def test_verify_two_factor_code_invalid(client: AsyncClient, db_session: Session):
    """
    Test 2FA code verification with an invalid code.
    """
    # Create a user with 2FA enabled and a verification token
    user_data = {
        "username": "invalid2fauser",
        "email": "invalid2fa@example.com",
        "password": "invalid2fapassword"
    }
    user_in_db = user_crud.create_user(db_session, UserCreate(
        username=user_data["username"],
        email=user_data["email"],
        password=user_data["password"]
    ))
    user_in_db.is_two_factor_enabled = True
    user_in_db.email_verification_token = "123456"
    user_in_db.email_verification_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    db_session.add(user_in_db)
    db_session.commit()
    db_session.refresh(user_in_db)

    response = await client.post(
        "/api/v1/users/token/2fa",
        json={"username": user_data["username"], "code": "wrongcode"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired 2FA code"

@pytest.mark.anyio
async def test_verify_two_factor_code_expired(client: AsyncClient, db_session: Session):
    """
    Test 2FA code verification with an expired code.
    """
    # Create a user with 2FA enabled and an expired verification token
    user_data = {
        "username": "expired2fauser",
        "email": "expired2fa@example.com",
        "password": "expired2fapassword"
    }
    user_in_db = user_crud.create_user(db_session, UserCreate(
        username=user_data["username"],
        email=user_data["email"],
        password=user_data["password"]
    ))
    user_in_db.is_two_factor_enabled = True
    user_in_db.email_verification_token = "123456"
    user_in_db.email_verification_token_expires_at = datetime.now(timezone.utc) - timedelta(minutes=5) # Expired
    db_session.add(user_in_db)
    db_session.commit()
    db_session.refresh(user_in_db)

    response = await client.post(
        "/api/v1/users/token/2fa",
        json={"username": user_data["username"], "code": "123456"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired 2FA code"
