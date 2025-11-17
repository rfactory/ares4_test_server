import pytest
from httpx import AsyncClient

@pytest.mark.anyio
async def test_create_user(client: AsyncClient):
    """
    Test user creation.
    """
    response = await client.post(
        "/api/v1/users/",
        json={"username": "testuser", "email": "test@example.com", "password": "testpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "password_hash" not in data # Ensure password hash is not returned

@pytest.mark.anyio
async def test_create_duplicate_user(client: AsyncClient):
    """
    Test creating a user with a duplicate username or email.
    """
    # Create a user first
    await client.post(
        "/api/v1/users/",
        json={"username": "testuser2", "email": "test2@example.com", "password": "testpassword"},
    )
    
    # Try to create a user with the same email
    response = await client.post(
        "/api/v1/users/",
        json={"username": "anotheruser", "email": "test2@example.com", "password": "testpassword"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

@pytest.mark.anyio
async def test_read_user(client: AsyncClient):
    """
    Test reading a user's details.
    """
    # Create a user first
    response = await client.post(
        "/api/v1/users/",
        json={"username": "testuser3", "email": "test3@example.com", "password": "testpassword"},
    )
    assert response.status_code == 200
    
    # Read the user
    response = await client.get("/api/v1/users/testuser3")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser3"
    assert data["email"] == "test3@example.com"
