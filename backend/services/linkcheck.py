"""Optional external link-reputation checks with a 24-hour DB cache.

All sources are optional. If no key/feed is configured the function returns
immediately and the core lookup works fully offline. Failures are swallowed
silently: an external outage must never break the public lookup.

Sources:
* Google Safe Browsing (key required)
* VirusTotal public API (key required, ~4 requests/min / 500 per day)
* OpenPhish community feed (no key, enable with OPENPHISH_FEED_URL)
* PhishTank feed (no key for the community CSV; set PHISHTANK_FEED_URL)
"""

from __future__ import annotations

import base64
import json
import os
import threading
import time
import urllib.parse
import urllib.request
from collections import deque
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

try:  # pragma: no cover
    from ..db.models import ExternalCheckCache
    from .normalize import NormalizedValue
    from .security import sanitize_text
    from .verdict import Signal
except (ImportError, ValueError):  # pragma: no cover
    from db.models import ExternalCheckCache
    from services.normalize import NormalizedValue
    from services.security import sanitize_text
    from services.verdict import Signal

SAFE_BROWSING_KEY = os.getenv("GOOGLE_SAFE_BROWSING_KEY", "").strip()
VIRUSTOTAL_KEY = os.getenv("VIRUSTOTAL_API_KEY", "").strip()
OPENPHISH_FEED_URL = os.getenv("OPENPHISH_FEED_URL", "").strip()
PHISHTANK_FEED_URL = os.getenv("PHISHTANK_FEED_URL", "").strip()
EXTERNAL_CHECKS_ENABLED = os.getenv("EXTERNAL_CHECKS_ENABLED", "true").lower() not in {"0", "false", "no"}
CACHE_HOURS = int(os.getenv("EXTERNAL_CACHE_HOURS", "24"))
VT_PER_MINUTE = int(os.getenv("VIRUSTOTAL_PER_MINUTE", "4"))
VT_PER_DAY = int(os.getenv("VIRUSTOTAL_PER_DAY", "500"))
USER_AGENT = "SPECTRA-UPI/2.0 (open-source UPI scam lookup)"

_VT_LOCK = threading.Lock()
_VT_TIMES: deque[float] = deque()
_VT_DAY = time.strftime("%Y-%m-%d")
_VT_DAY_COUNT = 0

_FEED_LOCK = threading.Lock()
_FEED_CACHE: dict[str, tuple[float, set[str]]] = {}


def _enabled_sources() -> list[str]:
    sources = []
    if SAFE_BROWSING_KEY:
        sources.append("safe_browsing")
    if VIRUSTOTAL_KEY:
        sources.append("virustotal")
    if OPENPHISH_FEED_URL:
        sources.append("openphish")
    if PHISHTANK_FEED_URL:
        sources.append("phishtank")
    return sources


def _cached(db: Session | None, url_hash: str, source: str) -> dict | None:
    if db is None:
        return None
    cutoff = datetime.now(timezone.utc) - timedelta(hours=CACHE_HOURS)
    row = (
        db.query(ExternalCheckCache)
        .filter(
            ExternalCheckCache.value_hash == url_hash,
            ExternalCheckCache.source == source,
            ExternalCheckCache.fetched_at >= cutoff,
        )
        .order_by(ExternalCheckCache.fetched_at.desc())
        .first()
    )
    if row is None:
        return None
    return row.result_json or None


def _store(db: Session | None, url_hash: str, source: str, result: dict, entity_id: int | None = None) -> None:
    if db is None:
        return
    db.add(
        ExternalCheckCache(
            entity_id=entity_id,
            value_hash=url_hash,
            source=source,
            result_json=result,
            fetched_at=datetime.now(timezone.utc),
        )
    )
    db.commit()


def _http_json(url: str, *, method: str = "GET", payload: dict | None = None, headers: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    all_headers = {"User-Agent": USER_AGENT}
    if payload is not None:
        all_headers["Content-Type"] = "application/json"
    all_headers.update(headers or {})
    request = urllib.request.Request(url, data=data, headers=all_headers, method=method)
    with urllib.request.urlopen(request, timeout=6) as response:
        return json.loads(response.read().decode("utf-8"))


def _check_safe_browsing(url: str) -> dict | None:
    if not SAFE_BROWSING_KEY:
        return None
    endpoint = "https://safebrowsing.googleapis.com/v4/threatMatches:find?key=" + urllib.parse.quote(SAFE_BROWSING_KEY)
    payload = {
        "client": {"clientId": "spectra-upi", "clientVersion": "2.0.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }
    try:
        body = _http_json(endpoint, method="POST", payload=payload)
    except Exception:
        return None
    matches = body.get("matches") or []
    return {
        "malicious": bool(matches),
        "threat_types": sorted({match.get("threatType", "THREAT") for match in matches}),
    }


def _vt_allow_request() -> bool:
    global _VT_DAY, _VT_DAY_COUNT
    today = time.strftime("%Y-%m-%d")
    with _VT_LOCK:
        if today != _VT_DAY:
            _VT_DAY = today
            _VT_DAY_COUNT = 0
            _VT_TIMES.clear()
        now = time.time()
        while _VT_TIMES and now - _VT_TIMES[0] > 60:
            _VT_TIMES.popleft()
        if _VT_DAY_COUNT >= VT_PER_DAY or len(_VT_TIMES) >= VT_PER_MINUTE:
            return False
        _VT_TIMES.append(now)
        _VT_DAY_COUNT += 1
        return True


def _check_virustotal(url: str) -> dict | None:
    if not VIRUSTOTAL_KEY or not _vt_allow_request():
        return None
    encoded = base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")
    try:
        body = _http_json(
            f"https://www.virustotal.com/api/v3/urls/{encoded}",
            headers={"x-apikey": VIRUSTOTAL_KEY, "Accept": "application/json"},
        )
    except Exception:
        return None
    stats = ((body.get("data") or {}).get("attributes") or {}).get("last_analysis_stats") or {}
    malicious = int(stats.get("malicious", 0)) + int(stats.get("suspicious", 0))
    return {
        "malicious": malicious > 0,
        "malicious_engines": int(stats.get("malicious", 0)),
        "suspicious_engines": int(stats.get("suspicious", 0)),
    }


def _load_feed(feed_url: str, source: str) -> set[str]:
    """Fetch a community feed at most once per cache window."""
    now = time.time()
    with _FEED_LOCK:
        cached = _FEED_CACHE.get(feed_url)
        if cached and now - cached[0] < CACHE_HOURS * 3600:
            return cached[1]
    request = urllib.request.Request(feed_url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            text = response.read().decode("utf-8", errors="ignore")
    except Exception:
        return set()

    entries: set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # OpenPhish is one URL per line; PhishTank CSV has the URL in column 2.
        if source == "phishtank" and "," in line:
            parts = line.split(",")
            line = parts[1] if len(parts) > 1 else line
        if line.startswith(("http://", "https://")):
            entries.add(line[:2048])
    with _FEED_LOCK:
        _FEED_CACHE[feed_url] = (now, entries)
    return entries


def _check_feed(url: str, feed_url: str, source: str) -> dict | None:
    if not feed_url:
        return None
    entries = _load_feed(feed_url, source)
    if not entries:
        return None
    return {"malicious": url in entries, "entries": len(entries)}


def _signal_for(source: str, result: dict) -> Signal | None:
    if not result:
        return None
    if not result.get("malicious"):
        return None
    labels = {
        "safe_browsing": "Google Safe Browsing lists this link",
        "virustotal": "VirusTotal engines flag this link",
        "openphish": "OpenPhish lists this link",
        "phishtank": "PhishTank lists this link",
    }
    detail = {
        "safe_browsing": "The link matched a Safe Browsing threat list ("
        + ", ".join(result.get("threat_types", []))
        + ").",
        "virustotal": f"{result.get('malicious_engines', 0)} security engines marked this URL malicious and "
        f"{result.get('suspicious_engines', 0)} marked it suspicious.",
        "openphish": "The URL appears in the OpenPhish community phishing feed.",
        "phishtank": "The URL appears in the PhishTank community feed.",
    }[source]
    return Signal(
        code=f"link:{source}",
        source="link",
        severity="high",
        label=labels[source],
        detail=sanitize_text(detail, 500),
    )


def check_url_signals(
    value: NormalizedValue,
    db: Session | None = None,
    entity_id: int | None = None,
) -> list[Signal]:
    """Return signals from any configured link-reputation source."""
    if value.type != "url" or not EXTERNAL_CHECKS_ENABLED:
        return []
    sources = _enabled_sources()
    if not sources:
        return []

    url = value.value
    url_hash = value.value_hash
    signals: list[Signal] = []

    for source in sources:
        result = _cached(db, url_hash, source)
        if result is None:
            try:
                if source == "safe_browsing":
                    result = _check_safe_browsing(url)
                elif source == "virustotal":
                    result = _check_virustotal(url)
                elif source == "openphish":
                    result = _check_feed(url, OPENPHISH_FEED_URL, "openphish")
                else:
                    result = _check_feed(url, PHISHTANK_FEED_URL, "phishtank")
            except Exception:
                result = None
            if result is not None:
                _store(db, url_hash, source, result, entity_id=entity_id)

        signal = _signal_for(source, result or {})
        if signal:
            signals.append(signal)

    return signals
