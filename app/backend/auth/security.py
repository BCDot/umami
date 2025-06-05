from datetime import datetime, timedelta
from typing import Optional, Dict

# In a real application, these should be complex and stored securely, likely in environment variables.
SECRET_KEY = "YOUR_VERY_SECRET_KEY_HERE"  # Replace with a strong, randomly generated key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Lifetime of access tokens

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generates a JWT access token.
    In a real implementation, this would use the python-jose library.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    # Placeholder: Real JWT encoding would happen here
    # from jose import jwt
    # encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    # return encoded_jwt

    print(f"[SECURITY_PLACEHOLDER] Encoding data for token: {to_encode}")
    return "dummy_jwt_token_for_" + data.get("sub", "unknown_user")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a hashed password.
    In a real implementation, this would use passlib.
    """
    # Placeholder: Real password verification would happen here
    # from passlib.context import CryptContext
    # pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    # return pwd_context.verify(plain_password, hashed_password)

    print(f"[SECURITY_PLACEHOLDER] Verifying '{plain_password}' against '{hashed_password}'")
    # This is a HUGELY INSECURE placeholder for demonstration purposes.
    # Never do this in a real application.
    return plain_password == hashed_password or (hashed_password == plain_password + "notreallyhashed")

# Example of how to hash a password (would typically be in user creation logic)
def get_password_hash(password: str) -> str:
    """
    Hashes a password using bcrypt.
    In a real implementation, this would use passlib.
    """
    # from passlib.context import CryptContext
    # pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    # return pwd_context.hash(password)
    print(f"[SECURITY_PLACEHOLDER] Hashing password '{password}'")
    return password + "notreallyhashed" # HUGELY INSECURE placeholder

if __name__ == "__main__":
    # Test token creation
    user_data = {"sub": "testuser@example.com", "role": "admin"}
    token = create_access_token(user_data)
    print(f"Generated Token: {token}")

    # Test password hashing and verification
    raw_password = "securepassword123"
    hashed = get_password_hash(raw_password)
    print(f"Hashed '{raw_password}': {hashed}")

    print(f"Verification (correct): {verify_password(raw_password, hashed)}")
    print(f"Verification (incorrect): {verify_password('wrongpassword', hashed)}")
    # Test against the "notreallyhashed" version from create_user example
    print(f"Verification (create_user example hash): {verify_password(raw_password, raw_password + 'notreallyhashed')}")

    # Note: The verify_password placeholder is very loose for testing.
    # In a real app, only the bcrypt hash should verify correctly.
