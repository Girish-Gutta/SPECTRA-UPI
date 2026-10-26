"""
backend/api/main.py
SPECTRA-UPI FastAPI application entry point
"""

import os
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

# Ensure backend root is in sys.path so db and api packages can always be found
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

try:
    from ..db.database import create_tables
    from .routes import router
    from .public import router as public_router
    from .admin import router as admin_router
    from .keys import router as keys_router
    from .dev import router as dev_router
    from ..services.ratelimit import limiter
except (ImportError, ValueError):
    from db.database import create_tables
    from api.routes import router
    from api.public import router as public_router
    from api.admin import router as admin_router
    from api.keys import router as keys_router
    from api.dev import router as dev_router
    from services.ratelimit import limiter


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
    description=(
        "Swift Payment Evaluation & Classification for Transaction Risk Analysis. "
        "Public scam lookup plus the existing authenticated transaction analyzer."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# ── Rate limiting (slowapi, in-memory) ────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS — restricted via env, permissive localhost defaults ──────────────
_origins_raw = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173",
)
_origins = [origin.strip() for origin in _origins_raw.split(",") if origin.strip()]
_allow_all = "*" in _origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _allow_all else _origins,
    # Browser credentials are not needed: JWTs travel in the Authorization
    # header, so wildcard origins remain safe.
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Add conservative security headers, mostly for API responses."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(self), microphone=()")
    if request.url.path.startswith("/api"):
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        )
    if request.url.scheme == "https":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


# ── Routers ───────────────────────────────────────────────────────────────
# Public scam lookup lives at /api (as documented in the README).
app.include_router(public_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(keys_router, prefix="/api")
# Existing authenticated transaction analyzer keeps its /api/v1 URLs.
app.include_router(router, prefix="/api/v1")
# Developer API with X-API-Key auth.
app.include_router(dev_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "project": "SPECTRA-UPI",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "public_lookup": "/api/lookup?q=name@handle",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
