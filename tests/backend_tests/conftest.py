import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession
from sqlalchemy.pool import StaticPool
from typing import Generator
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.backend.core.models import Base as CoreBase

# --- Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool  # Recommended for SQLite in-memory with tests
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# This fixture will be used by both direct DB tests and endpoint tests (via dependency override)
@pytest.fixture(scope="function")
def db() -> Generator[SQLAlchemySession, None, None]:
    CoreBase.metadata.create_all(bind=engine)  # Create tables for each test
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        CoreBase.metadata.drop_all(bind=engine)  # Drop tables after each test

# --- FastAPI TestClient Setup ---
minimal_app_for_testing = FastAPI()

# Import routers and their get_db dependencies
from app.backend.auth.endpoints import router as auth_router, get_db as auth_get_db_dependency
from app.backend.auth.security import get_db as security_get_db_dependency
from app.backend.routers.actions import router as actions_router, get_db as actions_get_db_dependency
from app.backend.routers.businesses import router as businesses_router, get_db as businesses_get_db_dependency
from app.backend.routers.communications import router as comms_router, get_db as comms_get_db_dependency

# Include routers in the minimal app
minimal_app_for_testing.include_router(auth_router, prefix="/api/v1")
minimal_app_for_testing.include_router(actions_router, prefix="/api/v1")
minimal_app_for_testing.include_router(businesses_router, prefix="/api/v1")
minimal_app_for_testing.include_router(comms_router, prefix="/api/v1")

# Store the original get_db functions to reset them later if needed, though pytest usually handles fixture teardown well.
original_dependencies = {
    "auth": auth_get_db_dependency,
    "security": security_get_db_dependency,
    "actions": actions_get_db_dependency,
    "businesses": businesses_get_db_dependency,
    "comms": comms_get_db_dependency,
}

@pytest.fixture(scope="function") # Changed client to function scope to align with db fixture
def client(db: SQLAlchemySession) -> Generator[TestClient, None, None]:
    """
    Function-scoped fixture for a FastAPI TestClient.
    Overrides `get_db` dependencies for all routers to use the function-scoped `db` fixture.
    """
    def get_db_override():
        try:
            yield db # Use the same db session provided by the 'db' fixture
        finally:
            # The 'db' fixture itself will handle closing/rolling back.
            # No db.close() here as it's managed by the 'db' fixture.
            pass

    # Apply overrides
    minimal_app_for_testing.dependency_overrides[auth_get_db_dependency] = get_db_override
    minimal_app_for_testing.dependency_overrides[security_get_db_dependency] = get_db_override
    minimal_app_for_testing.dependency_overrides[actions_get_db_dependency] = get_db_override
    minimal_app_for_testing.dependency_overrides[businesses_get_db_dependency] = get_db_override
    minimal_app_for_testing.dependency_overrides[comms_get_db_dependency] = get_db_override

    with TestClient(minimal_app_for_testing) as c:
        yield c

    # Clear overrides after the test
    minimal_app_for_testing.dependency_overrides.clear()

# Rename the old db_session to db to match the client's dependency name for clarity
# The `db` fixture above now serves both purposes.
# If any test files directly import `db_session` from conftest, they'll need to be updated to use `db`.
# Or, provide `db_session` as an alias for `db`.
@pytest.fixture(scope="function")
def db_session(db: SQLAlchemySession) -> SQLAlchemySession:
    """Alias for the 'db' fixture for tests that might still use 'db_session'."""
    return db
