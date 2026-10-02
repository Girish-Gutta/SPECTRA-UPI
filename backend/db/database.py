"""
backend/db/database.py
Database connection and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os
from pathlib import Path

# Absolute path so the DB always lands inside backend/ regardless of launch directory
_DB_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_DB = f"sqlite:///{_DB_DIR / 'spectra_upi.db'}"

# Swap DATABASE_URL env var for PostgreSQL in production
DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_DB)

# SQLite needs connect_args; PostgreSQL doesn't — handle both
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
