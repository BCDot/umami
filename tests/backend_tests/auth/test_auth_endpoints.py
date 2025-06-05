import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session # For type hinting the fixture
from app.backend.core import schemas, crud, models # For creating user and response validation
from app.backend.auth.security import get_password_hash # To hash password for test_user fixture if needed

# Prefix for API routes, matching conftest.py
API_V1_PREFIX = "/api/v1"

@pytest.fixture(scope="function") # function scope to ensure clean user for each test
def test_user_data() -> dict:
    return {
        "username": "testauthuser",
        "email": "testauthuser@example.com",
        "password": "testauthpassword"
    }

@pytest.fixture(scope="function")
def test_user(db_session: Session, test_user_data: dict) -> models.User:
    """Fixture to create a user in the database for login tests."""
    user_create_schema = schemas.UserCreate(**test_user_data)
    # crud.create_user already handles password hashing
    return crud.create_user(db=db_session, user=user_create_schema)


def test_register_user_success(client: TestClient, db_session: Session, test_user_data: dict):
    """Test successful user registration."""
    response = client.post(
        f"{API_V1_PREFIX}/auth/register",
        json={
            "username": test_user_data["username"] + "_register", # Ensure unique username
            "email": "register_" + test_user_data["email"], # Ensure unique email
            "password": test_user_data["password"]
        }
    )
    assert response.status_code == 200 # Assuming register endpoint returns 200 on success
    data = response.json()
    assert data["email"] == "register_" + test_user_data["email"]
    assert data["username"] == test_user_data["username"] + "_register"
    assert "id" in data
    assert "hashed_password" not in data # Ensure password is not returned

    # Verify user is in DB (optional, as CRUD is tested elsewhere, but good for endpoint integrity)
    user_in_db = crud.get_user_by_username(db_session, username=data["username"])
    assert user_in_db is not None
    assert user_in_db.email == data["email"]


def test_register_user_existing_email(client: TestClient, test_user: models.User, test_user_data: dict):
    """Test registration with an existing email."""
    response = client.post(
        f"{API_V1_PREFIX}/auth/register",
        json={
            "username": "anotherusername", # Different username
            "email": test_user_data["email"], # Existing email from test_user fixture
            "password": "anotherpassword"
        }
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_register_user_existing_username(client: TestClient, test_user: models.User, test_user_data: dict):
    """Test registration with an existing username."""
    response = client.post(
        f"{API_V1_PREFIX}/auth/register",
        json={
            "username": test_user_data["username"], # Existing username from test_user fixture
            "email": "another@example.com", # Different email
            "password": "anotherpassword"
        }
    )
    assert response.status_code == 400
    assert "Username already taken" in response.json()["detail"]


def test_login_for_access_token_success(client: TestClient, test_user: models.User, test_user_data: dict):
    """Test successful login and token generation."""
    login_data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"] # Plain password used for login form
    }
    response = client.post(f"{API_V1_PREFIX}/auth/token", data=login_data) # Use data for x-www-form-urlencoded

    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    # Further token validation could be done here if needed (e.g., decoding)


def test_login_for_access_token_incorrect_password(client: TestClient, test_user: models.User, test_user_data: dict):
    """Test login with incorrect password."""
    login_data = {
        "username": test_user_data["username"],
        "password": "wrongpassword"
    }
    response = client.post(f"{API_V1_PREFIX}/auth/token", data=login_data)
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]
    assert response.headers["www-authenticate"] == "Bearer"

def test_login_for_access_token_user_not_found(client: TestClient, test_user_data: dict):
    """Test login with a username that does not exist."""
    login_data = {
        "username": "nonexistentuser",
        "password": "anypassword"
    }
    response = client.post(f"{API_V1_PREFIX}/auth/token", data=login_data)
    assert response.status_code == 401 # Or 404 depending on how you want to handle it
    assert "Incorrect username or password" in response.json()["detail"]


def test_read_users_me_success(client: TestClient, test_user: models.User, test_user_data: dict):
    """Test accessing the /users/me endpoint with a valid token."""
    # 1. Login to get a token
    login_response = client.post(
        f"{API_V1_PREFIX}/auth/token",
        data={"username": test_user_data["username"], "password": test_user_data["password"]}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # 2. Access /users/me with the token
    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get(f"{API_V1_PREFIX}/auth/users/me", headers=headers)

    assert me_response.status_code == 200
    user_me_data = me_response.json()
    assert user_me_data["username"] == test_user_data["username"]
    assert user_me_data["email"] == test_user_data["email"]
    assert user_me_data["id"] == test_user.id


def test_read_users_me_no_token(client: TestClient):
    """Test accessing /users/me without a token."""
    response = client.get(f"{API_V1_PREFIX}/auth/users/me")
    assert response.status_code == 401 # Depends on FastAPI's default for missing OAuth2 token
    assert "Not authenticated" in response.json()["detail"] # Or similar default message


def test_read_users_me_invalid_token(client: TestClient):
    """Test accessing /users/me with an invalid token."""
    headers = {"Authorization": "Bearer invalidtoken"}
    response = client.get(f"{API_V1_PREFIX}/auth/users/me", headers=headers)
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]

# Placeholder for inactive user test - requires ability to set user.is_active = False
# def test_read_users_me_inactive_user(client: TestClient, db_session: Session, test_user_data: dict):
#     # Create user
#     user = crud.create_user(db_session, schemas.UserCreate(**test_user_data))
#     # Set user to inactive
#     user.is_active = False
#     db_session.commit()
#     db_session.refresh(user)

#     login_response = client.post(
#         f"{API_V1_PREFIX}/auth/token",
#         data={"username": test_user_data["username"], "password": test_user_data["password"]}
#     )
#     token = login_response.json()["access_token"]
#     headers = {"Authorization": f"Bearer {token}"}
#     me_response = client.get(f"{API_V1_PREFIX}/auth/users/me", headers=headers)
#     assert me_response.status_code == 400 # As per get_current_active_user
#     assert "Inactive user" in me_response.json()["detail"]
