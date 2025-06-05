import pytest
from datetime import timedelta, datetime, timezone
from jose import jwt, JWTError

from app.backend.auth.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

def test_get_password_hash():
    password = "testpassword"
    hashed_password = get_password_hash(password)
    assert hashed_password is not None
    assert hashed_password != password
    assert isinstance(hashed_password, str)

def test_verify_password():
    password = "testpassword123"
    hashed_password = get_password_hash(password)

    assert verify_password(password, hashed_password) is True
    assert verify_password("wrongpassword", hashed_password) is False

def test_verify_password_invalid_hash():
    password = "testpassword"
    invalid_hash = "thisisnotavalidbcrypthash"
    # Depending on bcrypt's behavior for malformed hashes, this might raise an error
    # or return False. passlib's bcrypt.verify handles malformed hashes by returning False.
    try:
        assert verify_password(password, invalid_hash) is False
    except ValueError as e:
        # bcrypt library itself might raise ValueError for malformed hash/salt
        print(f"ValueError caught during verify_password with invalid hash: {e}")
        pass # This is acceptable if the underlying library throws an error for malformed hashes
    except Exception as e:
        pytest.fail(f"Unexpected exception with invalid hash: {e}")


def test_create_access_token():
    data = {"sub": "testuser@example.com"}
    token = create_access_token(data)

    assert isinstance(token, str)

    # Basic check: try to decode to see if it's a valid JWT structure
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser@example.com"
        assert "exp" in payload

        # Check expiry is roughly correct
        expected_expiry = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        actual_expiry = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        # Allow a small delta for execution time
        assert abs((actual_expiry - expected_expiry).total_seconds()) < 5

    except JWTError as e:
        pytest.fail(f"Failed to decode generated token or token structure is invalid: {e}")

def test_create_access_token_custom_expiry():
    data = {"sub": "testuser_custom_exp@example.com"}
    custom_delta = timedelta(hours=1)
    token = create_access_token(data, expires_delta=custom_delta)

    assert isinstance(token, str)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser_custom_exp@example.com"

        expected_expiry = datetime.now(timezone.utc) + custom_delta
        actual_expiry = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        assert abs((actual_expiry - expected_expiry).total_seconds()) < 5

    except JWTError as e:
        pytest.fail(f"Failed to decode token with custom expiry: {e}")
