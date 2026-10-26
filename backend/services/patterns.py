"""Cheap, local risk signals that do not need any external API key.

These are heuristics, not accusations. They only ever raise the public verdict
to SUSPICIOUS and are always shown to the user as one factor among others.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from .normalize import NormalizedValue


@dataclass
class LocalSignal:
    code: str
    source: str  # pattern | url | qr
    severity: str  # low | medium | high
    label: str
    detail: str


# Keyword → existing fraud-pattern code. Intentionally conservative.
PATTERN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "FP-001": ("simswap", "sim-swap", "sim card", "simcard", "port out", "portout"),
    "FP-002": ("collect", "collect-request", "payrequest", "pay-request", "approve payment"),
    "FP-003": ("fakeqr", "fake-qr", "qr code", "scan-qr", "scanqr"),
    "FP-004": ("otp", "vishing", "one time password", "pin-verify", "verify-pin"),
    "FP-005": ("olx", "marketplace", "quikr", "classified", "buyer", "seller"),
    "FP-006": ("kyc", "kyc-expiry", "re-kyc", "rekyc", "account-block", "account block", "reactivate"),
    "FP-007": ("lottery", "prize", "lucky draw", "jackpot", "winner", "kbc", "cash reward"),
    "FP-008": ("anydesk", "teamviewer", "quicksupport", "screen share", "screenshare", "remote access"),
}

SUSPICIOUS_TLDS = {
    "zip",
    "mov",
    "top",
    "xyz",
    "click",
    "link",
    "rest",
    "work",
    "gq",
    "tk",
    "ml",
    "cf",
    "buzz",
    "monster",
}

SHORTENERS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "ow.ly",
    "is.gd",
    "buff.ly",
    "cutt.ly",
    "rb.gy",
    "shorturl.at",
}

PHISHING_WORDS = (
    "kyc",
    "verify",
    "verification",
    "login",
    "signin",
    "update",
    "refund",
    "reward",
    "prize",
    "lottery",
    "wallet",
    "upi",
    "bank",
    "secure",
    "account",
    "blocked",
    "reactivate",
    "support",
    "cashback",
    "collect",
)


def _targets(value: NormalizedValue) -> tuple[str, str]:
    """Return (handle-ish text, path/query-ish text) to scan for keywords."""
    if value.type == "url":
        parts = urlsplit(value.value)
        return (parts.hostname or ""), f"{parts.path}?{parts.query}"
    if value.type == "qr_payload":
        return value.value, value.value
    if value.type == "upi_id":
        local, _, handle = value.value.partition("@")
        # Handles like @okicici are legitimate; scanning them would create
        # constant false positives. Only inspect the username part.
        return local, handle
    return value.value, ""


def pattern_signals(value: NormalizedValue) -> list[LocalSignal]:
    primary, secondary = _targets(value)
    haystack = f"{primary} {secondary}".lower()
    signals: list[LocalSignal] = []
    for code, keywords in PATTERN_KEYWORDS.items():
        matched = next((kw for kw in keywords if kw in haystack), None)
        if matched:
            signals.append(
                LocalSignal(
                    code=f"pattern:{code}",
                    source="pattern",
                    severity="medium",
                    label="Name or link resembles a known scam pattern",
                    detail=(
                        f'The text contains "{matched}", which is commonly used in '
                        f"{code} frauds. Pattern matches alone are not proof of fraud."
                    ),
                )
            )
    return signals


def url_signals(value: NormalizedValue) -> list[LocalSignal]:
    """Heuristics that catch obvious phishing links without any API key."""
    if value.type != "url":
        return []

    parts = urlsplit(value.value)
    host = (parts.hostname or "").lower()
    path = (parts.path or "").lower()
    query = (parts.query or "").lower()
    signals: list[LocalSignal] = []

    if value.details.get("host_is_ip"):
        signals.append(
            LocalSignal(
                code="url:ip-host",
                source="url",
                severity="high",
                label="Link uses a raw IP address",
                detail="Legitimate banks and payment apps almost never send links that use an IP address instead of a domain.",
            )
        )

    if host.startswith("xn--") or ".xn--" in host:
        signals.append(
            LocalSignal(
                code="url:punycode",
                source="url",
                severity="medium",
                label="Link uses an encoded international domain",
                detail="Punycode domains can visually imitate a familiar brand. Check the spelling carefully.",
            )
        )

    if value.details.get("has_userinfo"):
        signals.append(
            LocalSignal(
                code="url:userinfo",
                source="url",
                severity="high",
                label="Link hides its real destination",
                detail="The part before '@' is not the website; the real host is after it.",
            )
        )

    tld = host.rsplit(".", 1)[-1] if "." in host else ""
    if tld in SUSPICIOUS_TLDS:
        signals.append(
            LocalSignal(
                code="url:tld",
                source="url",
                severity="medium",
                label=f"Link uses a frequently abused .{tld} domain",
                detail="This top-level domain is common in throwaway phishing sites. It is not proof by itself.",
            )
        )

    if host in SHORTENERS:
        signals.append(
            LocalSignal(
                code="url:shortener",
                source="url",
                severity="medium",
                label="Shortened link hides the destination",
                detail="Expand the link before opening it. Shorteners are often used to disguise phishing pages.",
            )
        )

    keyword = next((word for word in PHISHING_WORDS if word in path or word in query), None)
    if keyword:
        signals.append(
            LocalSignal(
                code="url:keyword",
                source="url",
                severity="medium",
                label="Link mentions a payment or verification action",
                detail=f'The link contains "{keyword}". Banks do not ask you to verify KYC or receive money through a link.',
            )
        )

    if parts.scheme == "http":
        signals.append(
            LocalSignal(
                code="url:no-https",
                source="url",
                severity="low",
                label="Link is not encrypted (http)",
                detail="Payment and bank pages should use https. Avoid entering personal details on an http page.",
            )
        )

    labels = host.split(".")
    if len(labels) >= 5:
        signals.append(
            LocalSignal(
                code="url:subdomains",
                source="url",
                severity="low",
                label="Link has an unusually deep subdomain chain",
                detail="Attackers often put a trusted brand name in a subdomain of a domain they control.",
            )
        )

    return signals


def all_local_signals(value: NormalizedValue) -> list[LocalSignal]:
    return pattern_signals(value) + url_signals(value)
