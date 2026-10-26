import os
import tempfile
from pathlib import Path

import pytest

# Configure the test environment *before* importing the application so the
# database engine and feature flags are created against a throwaway SQLite DB.
_TEST_DIR = Path(tempfile.mkdtemp(prefix="spectra-upi-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TEST_DIR / 'test.db').as_posix()}"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["CAPTCHA_DISABLED"] = "true"
os.environ["DEMO_DATA_ENABLED"] = "true"
os.environ["REPORTER_HASH_SALT"] = "test-salt"

from fastapi.testclient import TestClient  # noqa: E402

from db.database import engine  # noqa: E402
from db.models import Base  # noqa: E402
from db.seed import seed_all  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_database():
    """Every test gets a clean, seeded database."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_all()
    yield


@pytest.fixture
def client():
    from api.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session():
    from db.database import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
