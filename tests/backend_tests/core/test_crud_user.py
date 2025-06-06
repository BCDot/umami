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

    # Verify password correctly using the security utility
    from app.backend.auth.security import verify_password
    assert verify_password(user_password, created_user.hashed_password) is True
    assert created_user.hashed_password != user_password # Ensure it's not plain text

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


# --- Fixture for User Tests ---
@pytest.fixture(scope="function")
def test_user(db_session: Session) -> models.User:
    """Fixture to create a user in the database for user CRUD tests."""
    user_data = {
        "username": "crudtestuser",
        "email": "crudtestuser@example.com",
        "password": "crudtestpassword"
    }
    user_create_schema = schemas.UserCreate(**user_data)
    return crud.create_user(db=db_session, user=user_create_schema)

# --- User Update and Delete Tests ---

def test_update_user_details(db_session: Session, test_user: models.User):
    """Test updating user's email and is_active status."""
    update_data = schemas.UserUpdate(
        email="updatedcruduser@example.com",
        is_active=False
    )
    updated_user = crud.update_user(db=db_session, user_id=test_user.id, user_update=update_data)

    assert updated_user is not None
    assert updated_user.email == "updatedcruduser@example.com"
    assert updated_user.is_active is False
    assert updated_user.username == test_user.username # Username should not change by this update

    # Fetch again to confirm persistence
    refetched_user = crud.get_user(db=db_session, user_id=test_user.id)
    assert refetched_user is not None
    assert refetched_user.email == "updatedcruduser@example.com"
    assert refetched_user.is_active is False

def test_update_user_password(db_session: Session, test_user: models.User):
    """Test updating user's password."""
    from app.backend.auth.security import verify_password # For verification

    old_password = "crudtestpassword" # Original password from fixture
    new_password = "newcrudpassword123"

    update_data = schemas.UserUpdate(password=new_password)
    updated_user = crud.update_user(db=db_session, user_id=test_user.id, user_update=update_data)

    assert updated_user is not None
    assert updated_user.id == test_user.id

    # Verify the new password works
    assert verify_password(new_password, updated_user.hashed_password) is True
    # Verify the old password no longer works (important!)
    assert verify_password(old_password, updated_user.hashed_password) is False

    # Fetch again to confirm hash is stored
    refetched_user = crud.get_user(db=db_session, user_id=test_user.id)
    assert refetched_user is not None
    assert verify_password(new_password, refetched_user.hashed_password) is True

def test_update_user_no_changes(db_session: Session, test_user: models.User):
    """Test updating user with an empty update schema."""
    update_data = schemas.UserUpdate() # No fields set
    updated_user = crud.update_user(db=db_session, user_id=test_user.id, user_update=update_data)

    assert updated_user is not None
    assert updated_user.email == test_user.email # Should remain unchanged
    assert updated_user.username == test_user.username # Should remain unchanged
    assert updated_user.is_active == test_user.is_active # Should remain unchanged

def test_delete_user_soft_delete(db_session: Session, test_user: models.User):
    """Test soft deleting a user (setting is_active to False)."""
    # Ensure user is active first
    assert test_user.is_active is True

    deleted_user = crud.delete_user(db=db_session, user_id=test_user.id)

    assert deleted_user is not None
    assert deleted_user.is_active is False
    assert deleted_user.id == test_user.id

    # Fetch again to confirm is_active status in DB
    refetched_user = crud.get_user(db=db_session, user_id=test_user.id)
    assert refetched_user is not None
    assert refetched_user.is_active is False
