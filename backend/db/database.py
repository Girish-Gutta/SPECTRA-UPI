"""
backend/db/database.py
Database connection and session management.

The startup path is intentionally conservative:

1. ``Base.metadata.create_all`` creates any missing tables (never drops).
2. ``_migrate_missing_columns`` adds columns introduced after a database was
   first created (e.g. ``users.role``).
3. ``_seed_reference_data`` loads the scam-type catalogue, laws, helplines and
   clearly-labelled demo rows. All seed operations are idempotent.

This works on both SQLite (local) and PostgreSQL (free hosted tier). Alembic
is provided separately for explicit production migrations.
"""

import os
from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from .models import Base

# Absolute path so the DB always lands inside backend/ regardless of launch directory
_DB_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_DB = f"sqlite:///{_DB_DIR / 'spectra_upi.db'}"

# Swap DATABASE_URL env var for PostgreSQL in production
DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_DB)

# SQLite needs connect_args; PostgreSQL doesn't — handle both
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables() -> None:
    """Create missing tables, add missing columns, then seed reference data."""
    Base.metadata.create_all(bind=engine)
    _migrate_missing_columns()
    _seed_reference_data()


def _default_sql(col) -> str | None:
    """Render a portable ``DEFAULT`` clause for an ``ALTER TABLE ADD COLUMN``."""
    default = col.server_default
    if default is None:
        return None
    arg = getattr(default, "arg", None)
    if arg is None:
        return None

    # SQLAlchemy wraps string defaults in a TextClause.
    value = getattr(arg, "text", arg)
    if not isinstance(value, str):
        return str(value)

    upper = value.strip().upper()
    if upper in {"NULL", "CURRENT_TIMESTAMP", "TRUE", "FALSE"}:
        return value

    # Numeric defaults are safe unquoted.
    try:
        float(value)
        return value
    except ValueError:
        pass

    return "'" + value.replace("'", "''") + "'"


def _migrate_missing_columns() -> None:
    """
    Lightweight migration: if a table exists but is missing columns that the
    ORM models define (e.g. an older spectra_upi.db on disk), ALTER TABLE to
    add them so the app keeps working after model updates.

    Only additive changes are made — no table or column is ever dropped.
    """
    insp = inspect(engine)
    dialect = engine.dialect

    for table in Base.metadata.tables.values():
        if not insp.has_table(table.name):
            continue
        existing = {c["name"] for c in insp.get_columns(table.name)}
        for col in table.columns:
            if col.name in existing:
                continue

            col_type = col.type.compile(dialect=dialect)
            ddl = f"ALTER TABLE {table.name} ADD COLUMN {col.name} {col_type}"
            default_sql = _default_sql(col)
            if default_sql is not None:
                ddl += f" DEFAULT {default_sql}"

            with engine.begin() as conn:
                conn.exec_driver_sql(ddl)
            print(f"[MIGRATE] {table.name}.{col.name} added ({col_type})")


def _seed_reference_data() -> None:
    """Seed scam types, laws, helplines and demo rows (idempotent)."""
    try:
        from .seed import seed_all

        seed_all()
    except Exception as exc:  # pragma: no cover - startup guard
        # Never block the existing transaction analyzer if optional seed data
        # cannot be loaded. The error is printed for local debugging.
        print(f"[SEED] warning: {exc}")


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
