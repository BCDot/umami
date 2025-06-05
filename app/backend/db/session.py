from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import SQLALCHEMY_DATABASE_URL # Import the configured URL

# Determine if connect_args are needed (for SQLite)
connect_args = {}
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args
    # For production with PostgreSQL, you might want to configure pool size, etc.
    # pool_size=10,
    # max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    FastAPI dependency to get a database session.
    Ensures the database session is always closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Optional: Function to create tables (e.g., for initial setup if not using Alembic for everything)
# from app.backend.core.models import Base # Assuming your Base is accessible here
# def create_db_and_tables():
#     Base.metadata.create_all(bind=engine)
