"""
backend/api/main.py
SPECTRA-UPI FastAPI application entry point
"""

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Ensure backend root is in sys.path so db and api packages can always be found
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

try:
    from ..db.database import create_tables
    from .routes import router
except (ImportError, ValueError):
    from db.database import create_tables
    from api.routes import router


# Ensure Windows consoles don't crash on Unicode characters
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup."""
    create_tables()
    print("[OK] SPECTRA-UPI API started - DB tables ready")
    yield
    print("SPECTRA-UPI API shutting down")


app = FastAPI(
    title="SPECTRA-UPI API",
    description="Swift Payment Evaluation & Classification for Transaction Risk Analysis",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS — allow frontend (file:// or localhost dev server) ───────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount all routes ──────────────────────────────────────────────────────
app.include_router(router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "project": "SPECTRA-UPI",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
