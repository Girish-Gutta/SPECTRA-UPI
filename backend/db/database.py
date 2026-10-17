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
    """Create all tables if they don't exist, then add any missing columns."""
    Base.metadata.create_all(bind=engine)
    _migrate_missing_columns()


def _migrate_missing_columns():
    """
    Lightweight SQLite migration: if a table exists but is missing columns
    that the ORM models define (e.g. an older spectra_upi.db on disk),
    ALTER TABLE to add them so the app keeps working after model updates.
    """
    from sqlalchemy import inspect
    from sqlalchemy.dialects import sqlite

    insp = inspect(engine)
    for table in Base.metadata.tables.values():
        if not insp.has_table(table.name):
            continue
        existing = {c["name"] for c in insp.get_columns(table.name)}
        missing = [c for c in table.columns if c.name not in existing]
        for col in missing:
            col_type = col.type.compile(dialect=sqlite.dialect())
            with engine.begin() as conn:
                conn.exec_driver_sql(
                    f"ALTER TABLE {table.name} ADD COLUMN {col.name} {col_type}"
                )
            print(f"[MIGRATE] {table.name}.{col.name} added ({col_type})")


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
