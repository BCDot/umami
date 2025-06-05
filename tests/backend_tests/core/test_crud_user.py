import pytest
from sqlalchemy.orm import Session # This is the specific Session type from SQLAlchemy
from app.backend.core import crud
from app.backend.core import schemas
from app.backend.core import models # To access models.User if needed for type checks, etc.

def test_create_and_get_user(db_session: Session):
    """
    Test creating a new user and retrieving it by ID.
    """
    user_email = "testuser@example.com"
    user_username = "testusername"
    user_password = "testpassword"

    user_in = schemas.UserCreate(
        email=user_email,
        username=user_username,
        password=user_password,
        is_active=True # Explicitly set, though schema has default
    )

    # Create user
    created_user = crud.create_user(db=db_session, user=user_in)

    assert created_user is not None
    assert created_user.email == user_email
    assert created_user.username == user_username
    assert created_user.id is not None
    assert created_user.is_active is True
    # Check if password was "hashed" (using placeholder logic from security.py)
    assert created_user.hashed_password == user_password + "notreallyhashed"

    # Get user by ID
    retrieved_user_by_id = crud.get_user(db=db_session, user_id=created_user.id)

    assert retrieved_user_by_id is not None
    assert retrieved_user_by_id.email == user_email
    assert retrieved_user_by_id.id == created_user.id
    assert retrieved_user_by_id.username == user_username

def test_get_user_by_email(db_session: Session):
    """
    Test retrieving a user by their email address.
    """
    user_email = "test_by_email@example.com"
    user_username = "test_by_email_user"
    user_password = "testpassword_email"

    user_in = schemas.UserCreate(
        email=user_email,
        username=user_username,
        password=user_password
    )

    # Create user first
    created_user = crud.create_user(db=db_session, user=user_in)
    assert created_user is not None # Ensure creation was successful

    # Get user by email
    retrieved_user = crud.get_user_by_email(db=db_session, email=user_email)

    assert retrieved_user is not None
    assert retrieved_user.email == user_email
    assert retrieved_user.id == created_user.id
    assert retrieved_user.username == user_username

def test_get_user_by_username(db_session: Session):
    """
    Test retrieving a user by their username.
    """
    user_email = "test_by_username@example.com"
    user_username = "test_by_username_user"
    user_password = "testpassword_username"

    user_in = schemas.UserCreate(
        email=user_email,
        username=user_username,
        password=user_password
    )
    created_user = crud.create_user(db=db_session, user=user_in)
    assert created_user is not None

    retrieved_user = crud.get_user_by_username(db=db_session, username=user_username)
    assert retrieved_user is not None
    assert retrieved_user.username == user_username
    assert retrieved_user.email == user_email
    assert retrieved_user.id == created_user.id

def test_get_nonexistent_user(db_session: Session):
    """
    Test retrieving a non-existent user returns None.
    """
    retrieved_user_by_id = crud.get_user(db=db_session, user_id=99999)
    assert retrieved_user_by_id is None

    retrieved_user_by_email = crud.get_user_by_email(db=db_session, email="noone@example.com")
    assert retrieved_user_by_email is None

    retrieved_user_by_username = crud.get_user_by_username(db=db_session, username="nonexistentuser")
    assert retrieved_user_by_username is None
