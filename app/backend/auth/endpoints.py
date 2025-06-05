from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # OAuth2PasswordBearer is in security.py
from sqlalchemy.orm import Session
from datetime import timedelta # Used for token expiry calculation
from typing import List # For TokenData scopes, though not directly used in these endpoints yet

from app.backend.core import crud, schemas, models
from app.backend.auth import security # Imports verify_password, create_access_token, get_current_active_user, oauth2_scheme
# Placeholder for get_db dependency - replace with your actual DB session provider
# This should be the same as used in security.py
def get_db():
    print("[AUTH_ENDPOINTS_PLACEHOLDER] get_db() called, returning None for now.")
    yield None


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.post("/register", response_model=schemas.User)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    - Checks if email or username already exists.
    - Hashes password via crud.create_user (which uses security.get_password_hash).
    - Creates the user in the database.
    """
    if not db:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not configured")

    db_user_by_email = crud.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    db_user_by_username = crud.get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    created_user = crud.create_user(db=db, user=user)
    return created_user


@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login for access token (standard OAuth2 password flow).
    - Fetches user by username.
    - Verifies password.
    - Creates and returns a JWT access token.
    """
    if not db:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not configured")

    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username, "scopes": form_data.scopes}, # "sub" should be a unique identifier, usually username or email
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(security.get_current_active_user)):
    """
    Fetch the current authenticated and active user.
    This is an example of a protected endpoint.
    """
    return current_user

# Token and TokenData schemas are expected to be in app.backend.core.schemas
# If they were defined locally, they'd look like this:
# class Token(schemas.BaseModel): # Assuming BaseModel is imported from pydantic or schemas module
#     access_token: str
#     token_type: str

# class TokenData(schemas.BaseModel):
#     username: Optional[str] = None
#     scopes: List[str] = []
