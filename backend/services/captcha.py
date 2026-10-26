"""Cloudflare Turnstile verification (server-side).

Skipped automatically when ``CAPTCHA_DISABLED=true`` or when no secret key is
configured, so local development and core features work without any account.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

TURNSTILE_SECRET = os.getenv("TURNSTILE_SECRET_KEY", "").strip()
CAPTCHA_DISABLED = os.getenv("CAPTCHA_DISABLED", "false").lower() in {"1", "true", "yes"}
VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def captcha_required() -> bool:
    return bool(TURNSTILE_SECRET) and not CAPTCHA_DISABLED


def verify_turnstile(token: str | None, remote_ip: str | None = None) -> tuple[bool, str]:
    """Return ``(ok, reason)``.

    No key configured → success with reason ``skipped``. A configured key with
    a missing/invalid token fails closed.
    """
    if CAPTCHA_DISABLED:
        return True, "skipped"
    if not TURNSTILE_SECRET:
        return True, "skipped"
    if not token:
        return False, "CAPTCHA verification is required"

    payload = {"secret": TURNSTILE_SECRET, "response": token}
    if remote_ip:
        payload["remoteip"] = remote_ip

    request = urllib.request.Request(
        VERIFY_URL,
        data=urllib.parse.urlencode(payload).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=6) as response:
            body = json.loads(response.read().decode("utf-8"))
    except Exception:
        # Never leak provider details to the client.
        return False, "CAPTCHA verification is temporarily unavailable. Please try again."

    if body.get("success"):
        return True, "verified"
    return False, "CAPTCHA verification failed. Please retry the challenge."
