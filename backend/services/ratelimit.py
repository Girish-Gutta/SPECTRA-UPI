"""slowapi rate limiting with in-memory storage (no Redis required)."""

from __future__ import annotations

import os

from slowapi import Limiter

from .security import api_key_rate_key, reporter_rate_key

RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() not in {"0", "false", "no"}

limiter = Limiter(
    # Hash the client IP before it reaches the in-memory limiter so even
    # rate-limit keys never contain a raw address.
    key_func=reporter_rate_key,
    storage_uri="memory://",
    enabled=RATE_LIMIT_ENABLED,
    headers_enabled=True,
    # Never crash a request because the limiter itself had a problem.
    swallow_errors=True,
)

LOOKUP_LIMIT = os.getenv("LOOKUP_RATE_LIMIT", "60/minute")
REPORT_LIMIT = os.getenv("REPORT_RATE_LIMIT", "5/hour")
DISPUTE_LIMIT = os.getenv("DISPUTE_RATE_LIMIT", "3/hour")
API_KEY_LIMIT = os.getenv("API_KEY_RATE_LIMIT", "60/minute")


def report_key(request) -> str:
    return reporter_rate_key(request)


def api_key(request) -> str:
    return api_key_rate_key(request)
