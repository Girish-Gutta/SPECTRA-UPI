"""Security helpers: salted reporter hashes, input sanitising, API-key hashing.

No raw IP address is ever stored. ``reporter_hash`` is HMAC-SHA256 over the
client IP with a server-side salt, used only for duplicate detection and
per-reporter rate limiting.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
from urllib.parse import urlsplit

from fastapi import Request

REPORTER_SALT = os.getenv("REPORTER_HASH_SALT", "dev-only-reporter-salt-change-me")
TRUST_PROXY_HEADERS = os.getenv("TRUST_PROXY_HEADERS", "false").lower() in {"1", "true", "yes"}

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def client_ip(request: Request) -> str:
    """Best-effort client IP.

    Forwarded headers are only trusted when TRUST_PROXY_HEADERS=true, because
    otherwise anyone can spoof them and bypass rate limits.
    """
    if TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def hash_reporter(ip: str) -> str:
    """Return a stable salted hash, never the IP itself."""
    return hmac.new(REPORTER_SALT.encode("utf-8"), ip.encode("utf-8"), hashlib.sha256).hexdigest()


def reporter_rate_key(request: Request) -> str:
    return hash_reporter(client_ip(request))


def api_key_rate_key(request: Request) -> str:
    raw = request.headers.get("x-api-key", "anonymous")
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_api_key() -> str:
    return "spk_" + secrets.token_urlsafe(32)


def sanitize_text(value: str | None, max_length: int, *, allow_newlines: bool = True) -> str:
    """Remove control characters and enforce a hard length limit.

    HTML is never rendered by the API or the React frontend, so escaping is
    not required. We do strip control characters to keep logs and JSON clean.
    """
    if not value:
        return ""
    text = _CONTROL_CHARS.sub("", value)
    if allow_newlines:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Collapse runs of blank lines.
        text = re.sub(r"\n{3,}", "\n\n", text)
    else:
        text = re.sub(r"\s+", " ", text)
    return text.strip()[:max_length]


def is_safe_evidence_url(value: str | None) -> bool:
    """Evidence links are stored as text and never fetched by the server."""
    if not value:
        return False
    if len(value) > 2048:
        return False
    try:
        parts = urlsplit(value.strip())
    except ValueError:
        return False
    return (
        parts.scheme.lower() in {"http", "https"}
        and bool(parts.hostname)
        and "@" not in parts.netloc
    )


def is_valid_contact_email(value: str | None) -> bool:
    if not value:
        return True
    text = value.strip()
    return len(text) <= 254 and "@" in text and " " not in text and "." in text.split("@")[-1]
