import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession
from sqlalchemy.pool import StaticPool
from typing import Generator
from fastapi.testclient import TestClient

from app.backend.core.models import Base as CoreBase
from app.main import app as actual_app # Import the actual FastAPI app
from app.backend.db.session import get_db as central_get_db_dependency # The single get_db to override

# --- Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:" # Use a unique name for clarity if needed, e.g. "sqlite:///./test_db_for_conftest.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db() -> Generator[SQLAlchemySession, None, None]:
    CoreBase.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        CoreBase.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db: SQLAlchemySession) -> Generator[TestClient, None, None]:
    """
    Function-scoped fixture for a FastAPI TestClient.
    Overrides the central `get_db` dependency to use the function-scoped `db` fixture.
    """
    def get_db_override():
        try:
            yield db
        finally:
            pass # The 'db' fixture handles session closing and table dropping

    original_overrides = actual_app.dependency_overrides.copy()
    actual_app.dependency_overrides[central_get_db_dependency] = get_db_override

    with TestClient(actual_app) as c:
        yield c

    actual_app.dependency_overrides = original_overrides # Restore

@pytest.fixture(scope="function")
def db_session(db: SQLAlchemySession) -> SQLAlchemySession:
    """Alias for the 'db' fixture, mainly for any direct CRUD tests."""
    return db
