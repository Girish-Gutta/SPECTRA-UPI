"""Normalization and validation for public lookup values.

Supported types: UPI ID, URL, UPI QR payload and phone number.

The goal is a single canonical representation per identifier so that the same
fraudster cannot be listed twice with different casing, tracking parameters or
phone formatting. Everything here is pure Python and unit-tested.
"""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass, field
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

from .entity_service import value_hash

UPI_LOCAL_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,255}$")
UPI_HANDLE_RE = re.compile(r"^[a-z0-9][a-z0-9.-]{1,63}$")
PHONE_RE = re.compile(r"^\+?\d{7,15}$")
DOMAIN_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9-]{1,63}\.)+[a-z0-9-]{2,63}$")

VALID_TYPES = {"upi_id", "url", "qr_payload", "phone"}

# Query parameters that only exist for marketing/analytics. Removing them
# keeps the same page from being reported under several URLs.
TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "gclsrc",
    "igshid",
    "mc_cid",
    "mc_eid",
    "ref",
    "ref_src",
    "si",
    "yclid",
    "mkt_tok",
    "_hsenc",
    "_hsmi",
}


@dataclass
class NormalizedValue:
    """A canonical identifier plus display metadata."""

    type: str
    value: str
    input_value: str
    details: dict = field(default_factory=dict)

    @property
    def value_hash(self) -> str:
        return value_hash(self.value)

    @property
    def masked(self) -> str:
        return mask_value(self.value, self.type)


class NormalizationError(ValueError):
    """Raised when a value cannot be normalized safely."""


# ── Masking ───────────────────────────────────────────────────────────────


def mask_value(value: str, kind: str) -> str:
    """Mask an identifier for public lists.

    Detail pages show the full value the user searched for; aggregate/list
    views only ever receive this masked form.
    """
    if kind == "upi_id" and "@" in value:
        local, handle = value.split("@", 1)
        if len(local) <= 2:
            shown = (local[:1] or "*") + "***"
        else:
            shown = local[:2] + "****"
        return f"{shown}@{handle}"

    if kind == "phone":
        digits = re.sub(r"\D", "", value)
        if len(digits) <= 4:
            return "****"
        return "*" * (len(digits) - 4) + digits[-4:]

    if kind in {"url", "qr_payload"}:
        if kind == "url":
            try:
                parts = urlsplit(value)
                host = parts.hostname or value
                return f"{parts.scheme}://{mask_host(host)}{parts.path if len(parts.path) < 40 else '…'}"
            except ValueError:
                pass
        text = value if len(value) <= 20 else value[:8] + "…" + value[-6:]
        return re.sub(r"([a-z0-9._-])[a-z0-9._-]*@", r"\1***@", text, flags=re.I)

    return value[:2] + "***" if len(value) > 2 else "***"


def mask_host(host: str) -> str:
    labels = host.split(".")
    if len(labels) <= 2:
        return host[0] + "***." + ".".join(labels[1:]) if len(labels) == 2 else "***"
    return labels[0][0] + "***." + ".".join(labels[-2:])


# ── Type detection ────────────────────────────────────────────────────────


def detect_type(raw: str) -> str:
    """Best-effort type detection for ``type=auto``."""
    text = (raw or "").strip()
    if not text:
        raise NormalizationError("Enter a UPI ID, link, QR payload or phone number")

    if text.lower().startswith("upi://"):
        return "qr_payload"

    if _looks_like_url(text):
        return "url"

    if "@" in text and not text.startswith("@") and " " not in text:
        return "upi_id"

    if PHONE_RE.match(re.sub(r"[\s()\-]", "", text)):
        return "phone"

    # A bare domain such as "example.com" is treated as a URL.
    candidate = text.split("/", 1)[0].lower()
    if DOMAIN_RE.match(candidate):
        return "url"

    raise NormalizationError("Could not recognise this value. Use a UPI ID, http(s) link, UPI QR payload or phone number")


def _looks_like_url(text: str) -> bool:
    lowered = text.lower()
    return lowered.startswith(("http://", "https://"))


# ── UPI ───────────────────────────────────────────────────────────────────


def normalize_upi(raw: str) -> NormalizedValue:
    text = unquote((raw or "").strip()).lower()
    if text.count("@") != 1:
        raise NormalizationError("UPI ID must look like name@handle")
    local, handle = text.split("@", 1)
    local = local.strip()
    handle = handle.strip()
    if not UPI_LOCAL_RE.match(local):
        raise NormalizationError("Invalid UPI ID username")
    if not UPI_HANDLE_RE.match(handle):
        raise NormalizationError("Invalid UPI handle")
    value = f"{local}@{handle}"
    return NormalizedValue(type="upi_id", value=value, input_value=raw, details={"handle": handle})


# ── URL ───────────────────────────────────────────────────────────────────


def _is_tracking_param(key: str) -> bool:
    key = key.lower()
    return key in TRACKING_PARAMS or key.startswith("utm_")


def normalize_url(raw: str) -> NormalizedValue:
    text = (raw or "").strip()
    if not text:
        raise NormalizationError("URL is empty")
    if "://" not in text:
        text = "https://" + text

    try:
        parts = urlsplit(text)
    except ValueError as exc:
        raise NormalizationError("Invalid URL") from exc

    if parts.scheme.lower() not in {"http", "https"}:
        raise NormalizationError("Only http:// and https:// links are supported")
    if not parts.hostname:
        raise NormalizationError("URL has no host")

    # Drop credentials: they are a phishing signal and should not be stored.
    host = parts.hostname.lower()
    try:
        ipaddress.ip_address(host)
        host_is_ip = True
    except ValueError:
        host_is_ip = False

    if not host_is_ip and not DOMAIN_RE.match(host):
        raise NormalizationError("Invalid URL host")

    port = ""
    if parts.port and not (
        (parts.scheme.lower() == "http" and parts.port == 80)
        or (parts.scheme.lower() == "https" and parts.port == 443)
    ):
        port = f":{parts.port}"

    if host_is_ip and ":" in host:
        host = f"[{host}]"

    path = parts.path or "/"
    # Collapse duplicate slashes without changing path case (paths are
    # case-sensitive on most servers).
    path = re.sub(r"/{2,}", "/", path)
    params = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not _is_tracking_param(k)]
    params.sort(key=lambda item: (item[0], item[1]))
    query = urlencode(params, doseq=True)
    value = urlunsplit((parts.scheme.lower(), host + port, path, query, ""))

    if len(value) > 2048:
        raise NormalizationError("URL is too long (max 2048 characters)")
    return NormalizedValue(
        type="url",
        value=value,
        input_value=raw,
        details={
            "host": host,
            "scheme": parts.scheme.lower(),
            "path": path,
            "host_is_ip": host_is_ip,
            # Credentials are stripped from the canonical value but kept as a
            # boolean signal so the URL heuristic can flag them.
            "has_userinfo": "@" in parts.netloc,
        },
    )


# ── QR payload / UPI intent ───────────────────────────────────────────────


def parse_upi_payload(raw: str) -> dict | None:
    """Extract ``pa``, ``pn`` and ``am`` from a ``upi://pay?...`` payload."""
    text = (raw or "").strip()
    if not text.lower().startswith("upi://"):
        return None
    try:
        parts = urlsplit(text)
    except ValueError:
        return None
    if parts.netloc.lower() not in {"pay", "p2p", "p2m"}:
        return None
    params = {k.lower(): v for k, v in parse_qsl(parts.query, keep_blank_values=True)}
    pa = unquote(params.get("pa", "")).strip().lower()
    if not pa:
        return None
    return {
        "pa": pa,
        "pn": unquote(params.get("pn", "")).strip()[:100] or None,
        "am": unquote(params.get("am", "")).strip()[:20] or None,
    }


def normalize_qr(raw: str) -> NormalizedValue:
    payload = parse_upi_payload(raw)
    if payload is None:
        # Not a UPI intent: keep it as opaque QR text, length-limited.
        text = (raw or "").strip()
        if not text:
            raise NormalizationError("QR payload is empty")
        if len(text) > 2048:
            raise NormalizationError("QR payload is too long")
        # URLs and UPI IDs inside arbitrary QR text get their own type so
        # existing reports are reused.
        if _looks_like_url(text):
            return normalize_url(text)
        if "@" in text and " " not in text:
            try:
                return normalize_upi(text)
            except NormalizationError:
                pass
        return NormalizedValue(type="qr_payload", value=text, input_value=raw, details={"kind": "text"})

    # A UPI QR payload is ultimately a payment to a UPI ID. Store and search
    # the payee UPI ID so all QR variants collapse onto one entity.
    upi = normalize_upi(payload["pa"])
    upi.details.update({"qr": True, "payee_name": payload["pn"], "amount": payload["am"], "raw_payload": raw.strip()[:2048]})
    return upi


# ── Phone ─────────────────────────────────────────────────────────────────


def normalize_phone(raw: str) -> NormalizedValue:
    text = (raw or "").strip()
    plus = text.startswith("+")
    digits = re.sub(r"\D", "", text)
    if not digits or not PHONE_RE.match(("+" if plus else "") + digits):
        raise NormalizationError("Invalid phone number")
    if len(digits) == 10:
        value = "+91" + digits
    elif len(digits) == 11 and digits.startswith("0"):
        value = "+91" + digits[1:]
    elif len(digits) == 12 and digits.startswith("91"):
        value = "+" + digits
    elif plus:
        value = "+" + digits
    else:
        value = "+" + digits
    return NormalizedValue(type="phone", value=value, input_value=raw, details={})


# ── Public entry points ───────────────────────────────────────────────────


def normalize(raw: str, requested_type: str = "auto") -> NormalizedValue:
    """Normalize ``raw`` to one of the four canonical identifier types."""
    requested = (requested_type or "auto").lower()
    if requested not in VALID_TYPES | {"auto"}:
        raise NormalizationError("Unknown identifier type")
    kind = detect_type(raw) if requested == "auto" else requested

    if kind == "upi_id":
        return normalize_upi(raw)
    if kind == "url":
        return normalize_url(raw)
    if kind == "phone":
        return normalize_phone(raw)
    if kind == "qr_payload":
        return normalize_qr(raw)
    raise NormalizationError("Unknown identifier type")


def normalize_report_value(raw: str, requested_type: str = "auto") -> NormalizedValue:
    """Normalize a value submitted with a report.

    Reporting accepts the same four types. A UPI QR payload resolves to its
    payee UPI ID, so a QR scan and a typed UPI ID share one entity.
    """
    return normalize(raw, requested_type)
