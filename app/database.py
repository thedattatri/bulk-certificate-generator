import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Database URL: SQLite database file stored in the project root or configured directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "certificates.db")
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# SessionLocal is a factory to create independent database sessions for each request.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class from which all SQLAlchemy models inherit.
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a transactional database session per request.
    Ensures the session is automatically closed when the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
