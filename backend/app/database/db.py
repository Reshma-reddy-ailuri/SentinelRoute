import logging
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DATABASE_URL

logger = logging.getLogger(__name__)


def ensure_sqlite_parent_dir():
    """Ensure the SQLite directory exists for Render persistent storage."""
    if not DATABASE_URL.startswith("sqlite"):
        return

    parsed = urlparse(DATABASE_URL)
    if parsed.scheme != "sqlite" or not parsed.path:
        return

    db_path = Path(parsed.path)
    db_dir = db_path.parent
    if str(db_dir) != ".":
        db_dir.mkdir(parents=True, exist_ok=True)


ensure_sqlite_parent_dir()

# SQLite database setup with SQLAlchemy
# check_same_thread=False allows FastAPI multi-threaded request handlers to use the DB connection
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for API routes to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
