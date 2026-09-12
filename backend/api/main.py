"""
backend/api/main.py
SPECTRA-UPI FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from ..db.database import create_tables
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup."""
    create_tables()
    print("✅ SPECTRA-UPI API started — DB tables ready")
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
