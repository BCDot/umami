from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.hash import bcrypt # Changed from passlib.context CryptContext for direct bcrypt use
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# Assuming crud and models are in app.backend.core
from app.backend.core import crud, models, schemas
# Placeholder for get_db dependency - replace with your actual DB session provider
# This should be the same as used in other router files like auth/endpoints.py
def get_db():
    print("[SECURITY_PLACEHOLDER] get_db() called in security.py, returning None for now.")
    yield None # CRUD operations will not work without a real DB session.


# Configuration (should ideally come from environment variables via app.config)
SECRET_KEY = "your-super-secret-key-that-is-at-least-32-bytes-long"  # Replace with a strong, randomly generated key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Lifetime of access tokens

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token") # tokenUrl is relative to app root

def get_password_hash(password: str) -> str:
    """
    Hashes a password using bcrypt.
    """
    return bcrypt.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a hashed password using bcrypt.
    """
    return bcrypt.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generates a JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    """
    Decodes JWT token, validates it, and retrieves the user.
    This is a dependency to be used in protected endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not db: # Added for placeholder get_db
        print("[SECURITY_GET_CURRENT_USER_PLACEHOLDER] DB not configured. Cannot fetch user.")
        # This would normally prevent any user from being "found" if DB is None.
        # For placeholder testing, one might allow a dummy user if token is "dummy_jwt_token..."
        # However, the JWT decoding will fail first if the token isn't a real JWT.
        # If token is "dummy_jwt_token_for_testuser@example.com" (from old placeholder create_access_token)
        # this function will fail at jwt.decode.
        raise credentials_exception # Or handle differently if you want to allow unauthenticated access for some reason

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
        # token_scopes = payload.get("scopes", []) # Example for scope handling
    except JWTError:
        raise credentials_exception

    user = crud.get_user_by_username(db, username=username) # Or by email if 'sub' is email
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    """
    Dependency to get the current user and ensure they are active.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


if __name__ == "__main__":
    # Test password hashing and verification
    raw_password = "securepassword123"
    print(f"Raw password: {raw_password}")

    hashed = get_password_hash(raw_password)
    print(f"Hashed password: {hashed}")

    is_correct = verify_password(raw_password, hashed)
    print(f"Password verification (correct): {is_correct}")
    assert is_correct

    is_incorrect = verify_password("wrongpassword", hashed)
    print(f"Password verification (incorrect): {is_incorrect}")
    assert not is_incorrect

    # Test token creation
    user_data_for_token = {"sub": "testuser@example.com", "custom_claim": "example_value"}
    token = create_access_token(user_data_for_token)
    print(f"Generated JWT Token: {token}")

    # Example of how get_current_user would be (conceptually) tested
    # Requires a mock DB and a real token.
    # For now, this just shows the token.
    # To test get_current_user, you'd need a running FastAPI app or more complex mocking.
    try:
        decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"Decoded JWT Payload: {decoded_payload}")
        assert decoded_payload["sub"] == "testuser@example.com"
        assert "exp" in decoded_payload
    except JWTError as e:
        print(f"JWT Error during manual decode test: {e}")
