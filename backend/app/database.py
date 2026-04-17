from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging

logger = logging.getLogger(__name__)

# Use environment variable for DB URL, fallback to absolute path for SQLite
# Absolute path is necessary for many cloud environments like Hugging Face
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Force local sqlite if USE_LOCAL_SQLITE is true in .env
USE_LOCAL_SQLITE = os.getenv("USE_LOCAL_SQLITE", "false").lower() == "true"

def get_sqlite_url():
    """Determine the best SQLite URL, falling back to /tmp if the app dir is read-only."""
    default_path = os.path.join(os.path.dirname(BASE_DIR), "sql_app.db")
    db_dir = os.path.dirname(default_path)
    
    # Check if the directory is writable. If not, use /tmp (common on Hugging Face Spaces)
    if not os.access(db_dir, os.W_OK):
        tmp_path = "/tmp/sql_app.db"
        logger.warning(f"Directory {db_dir} is NOT writable. Falling back to {tmp_path}")
        return f"sqlite:///{tmp_path}"
    
    return f"sqlite:///{default_path}"

if USE_LOCAL_SQLITE:
    SQLALCHEMY_DATABASE_URL = get_sqlite_url()
    logger.info(f"Forcing local SQLite database.")
else:
    # Standard behavior: Use DATABASE_URL or fallback to writable SQLite path
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URL = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URL = get_sqlite_url()

logger.info(f"Connecting to database: {SQLALCHEMY_DATABASE_URL.split('@')[-1] if '@' in SQLALCHEMY_DATABASE_URL else SQLALCHEMY_DATABASE_URL}")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


