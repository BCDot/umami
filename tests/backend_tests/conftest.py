import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession # Renamed to avoid conflict
from typing import Generator

# Assuming your models are defined in app.backend.core.models
# Adjust the import path if your project structure is different.
from app.backend.core.models import Base as CoreBase # Give an alias if 'Base' is too generic

# Database setup for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"  # In-memory SQLite database

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} # check_same_thread is for SQLite
)

# Create a sessionmaker to generate sessions
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session() -> Generator[SQLAlchemySession, None, None]:
    """
    Pytest fixture to set up a database session for each test function.
    - Creates all tables before the test.
    - Yields a database session.
    - Drops all tables after the test.
    """
    # Create tables in the test database
    CoreBase.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db  # Provide the session to the test
    finally:
        db.close()
        # Drop all tables after the test
        CoreBase.metadata.drop_all(bind=engine)

# You can add other global fixtures here if needed, for example,
# a fixture to create a test client for FastAPI endpoints.
# from fastapi.testclient import TestClient
# from app.main import app # Assuming your FastAPI app instance is in app/main.py

# @pytest.fixture(scope="module")
# def client() -> Generator[TestClient, None, None]:
#     """
#     Pytest fixture for a FastAPI TestClient.
#     """
#     with TestClient(app) as c:
#         yield c
