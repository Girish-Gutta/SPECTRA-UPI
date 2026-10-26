"""Public, unauthenticated scam-lookup endpoints."""

from __future__ import annotations

import difflib
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

try:  # pragma: no cover
    from ..db import get_db
    from ..db.models import Dispute, Entity, Helpline, Law, Report, ScamType, User
    from ..services.captcha import verify_turnstile
    from ..services.entity_service import recalculate_entity, value_hash
    from ..services.explain import helplines_for, laws_for
    from ..services.lookup_service import perform_lookup
    from ..services.normalize import NormalizationError, mask_value, normalize
    from ..services.ratelimit import DISPUTE_LIMIT, LOOKUP_LIMIT, REPORT_LIMIT, limiter, report_key
    from ..services.security import (
        client_ip,
        hash_reporter,
        is_safe_evidence_url,
        is_valid_contact_email,
        sanitize_text,
    )
    from .auth import get_optional_user
    from .public_schemas import (
        DisputeCreate,
        DisputeCreated,
        LookupResponse,
        ReportCreate,
        ReportCreated,
    )
except (ImportError, ValueError):  # pragma: no cover
    from db import get_db
    from db.models import Dispute, Entity, Helpline, Law, Report, ScamType, User
    from services.captcha import verify_turnstile
    from services.entity_service import recalculate_entity, value_hash
    from services.explain import helplines_for, laws_for
    from services.lookup_service import perform_lookup
    from services.normalize import NormalizationError, mask_value, normalize
    from services.ratelimit import DISPUTE_LIMIT, LOOKUP_LIMIT, REPORT_LIMIT, limiter, report_key
    from services.security import (
        client_ip,
        hash_reporter,
        is_safe_evidence_url,
        is_valid_contact_email,
        sanitize_text,
    )
    from api.auth import get_optional_user
    from api.public_schemas import (
        DisputeCreate,
        DisputeCreated,
        LookupResponse,
        ReportCreate,
        ReportCreated,
    )

router = APIRouter(tags=["public"])

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@router.get("/lookup", response_model=LookupResponse)
@limiter.limit(LOOKUP_LIMIT)
def lookup(
    request: Request,
    response: Response,
    q: str = Query(..., min_length=2, max_length=2048, description="UPI ID, URL, QR payload or phone number"),
    entity_type: str = Query("auto", alias="type", pattern="^(auto|upi_id|url|qr_payload|phone)$"),
    db: Session = Depends(get_db),
    # Optional transaction context. The model runs only when both amount and
    # platform are supplied.
    amount: Optional[float] = Query(None, ge=0, le=200000),
    platform: Optional[str] = Query(None, max_length=50),
    tx_date: Optional[str] = Query(None, max_length=20),
    tx_time: Optional[str] = Query(None, max_length=10),
    location_change: bool = False,
    new_recipient: bool = True,
    failed_attempts: int = Query(0, ge=0, le=20),
    device_count: int = Query(1, ge=1, le=20),
    txn_freq_1h: int = Query(0, ge=0, le=100),
    txn_freq_24h: int = Query(0, ge=0, le=500),
    amount_z_score: float = Query(0.0, ge=0, le=100),
    amount_vs_recent: float = Query(0.0, ge=0, le=100),
    is_preferred_platform: bool = True,
):
    transaction = None
    if amount is not None and platform:
        transaction = {
            "amount": amount,
            "platform": platform,
            "tx_date": tx_date or "",
            "tx_time": tx_time or "",
            "location_change": location_change,
            "new_recipient": new_recipient,
            "failed_attempts": failed_attempts,
            "device_count": device_count,
            "txn_freq_1h": txn_freq_1h,
            "txn_freq_24h": txn_freq_24h,
            "amount_z_score": amount_z_score,
            "amount_vs_recent": amount_vs_recent,
            "is_preferred_platform": is_preferred_platform,
        }

    try:
        return perform_lookup(db, q, entity_type, transaction)
    except NormalizationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ── Reports ───────────────────────────────────────────────────────────────


@router.post("/reports", response_model=ReportCreated, status_code=201)
@limiter.limit(REPORT_LIMIT, key_func=report_key)
def create_report(
    request: Request,
    response: Response,
    body: ReportCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    ok, reason = verify_turnstile(body.captcha_token, client_ip(request))
    if not ok:
        raise HTTPException(status_code=400, detail=reason)

    try:
        normalized = normalize(body.entity_value, body.entity_type)
    except NormalizationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if db.get(ScamType, body.scam_type_code) is None:
        raise HTTPException(status_code=400, detail="Unknown scam type")

    if body.incident_date and body.incident_date > date.today():
        raise HTTPException(status_code=400, detail="Incident date cannot be in the future")

    if body.evidence_url and not is_safe_evidence_url(body.evidence_url):
        raise HTTPException(status_code=400, detail="Evidence link must be a valid http(s) URL")
    if not is_valid_contact_email(body.contact_email):
        raise HTTPException(status_code=400, detail="Invalid contact email")

    description = sanitize_text(body.description, 2000)
    if len(description) < 10:
        raise HTTPException(status_code=400, detail="Description is too short")

    reporter_hash = hash_reporter(client_ip(request))

    entity = (
        db.query(Entity)
        .filter(Entity.type == normalized.type, Entity.value_hash == normalized.value_hash)
        .first()
    )
    if entity is None:
        entity = Entity(
            type=normalized.type,
            value=normalized.value,
            value_hash=normalized.value_hash,
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
        )
        db.add(entity)
        db.flush()

    # Duplicate: same salted reporter hash + same entity within 24 hours.
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent = (
        db.query(Report)
        .filter(Report.entity_id == entity.id, Report.created_at >= cutoff)
        .all()
    )
    if any(report.reporter_hash == reporter_hash for report in recent):
        raise HTTPException(
            status_code=409,
            detail="You have already reported this identifier in the last 24 hours.",
        )

    # Near-identical wording is allowed but pushed to the front of the queue.
    near_duplicate = any(
        difflib.SequenceMatcher(None, description.lower(), (report.description or "").lower()).ratio() >= 0.9
        for report in recent
        if report.description
    )

    report = Report(
        entity_id=entity.id,
        scam_type_code=body.scam_type_code,
        amount_lost=body.amount_lost,
        incident_date=body.incident_date,
        description=description,
        evidence_url=body.evidence_url.strip() if body.evidence_url else None,
        reporter_user_id=current_user.id if current_user else None,
        reporter_hash=reporter_hash,
        contact_email=sanitize_text(body.contact_email, 254) if body.contact_email else None,
        priority_flag=bool(current_user or body.evidence_url or near_duplicate),
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    db.add(report)
    entity.last_seen = datetime.now(timezone.utc)
    db.flush()
    recalculate_entity(db, entity)
    db.commit()
    db.refresh(report)

    return ReportCreated(
        id=report.id,
        status=report.status,
        message=(
            "Thank you. Your report is pending review. It is not published and does not "
            "affect the public verdict until a moderator verifies it."
        ),
        masked_value=normalized.masked,
    )


# ── Disputes / takedown ───────────────────────────────────────────────────


@router.post("/disputes", response_model=DisputeCreated, status_code=201)
@limiter.limit(DISPUTE_LIMIT, key_func=report_key)
def create_dispute(
    request: Request,
    response: Response,
    body: DisputeCreate,
    db: Session = Depends(get_db),
):
    ok, reason = verify_turnstile(body.captcha_token, client_ip(request))
    if not ok:
        raise HTTPException(status_code=400, detail=reason)

    try:
        normalized = normalize(body.entity_value, body.entity_type)
    except NormalizationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not is_valid_contact_email(body.contact_email):
        raise HTTPException(status_code=400, detail="Invalid contact email")
    text = sanitize_text(body.reason, 2000)
    if len(text) < 20:
        raise HTTPException(status_code=400, detail="Please explain the dispute in at least 20 characters")

    entity = (
        db.query(Entity)
        .filter(Entity.type == normalized.type, Entity.value_hash == normalized.value_hash)
        .first()
    )
    if entity is None:
        entity = Entity(
            type=normalized.type,
            value=normalized.value,
            value_hash=normalized.value_hash,
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
        )
        db.add(entity)
        db.flush()

    # Same reporter cannot open unlimited disputes in a short window.
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    existing = (
        db.query(Dispute)
        .filter(
            Dispute.entity_id == entity.id,
            Dispute.created_at >= cutoff,
            Dispute.status == "open",
        )
        .count()
    )
    if existing >= 2:
        raise HTTPException(
            status_code=409,
            detail="A dispute for this identifier is already open. Please wait for a moderator.",
        )

    dispute = Dispute(
        entity_id=entity.id,
        contact_email=sanitize_text(body.contact_email, 254) if body.contact_email else None,
        reason=text,
        status="open",
        created_at=datetime.now(timezone.utc),
    )
    db.add(dispute)
    db.commit()
    db.refresh(dispute)

    return DisputeCreated(
        id=dispute.id,
        status=dispute.status,
        message=(
            "Your dispute has been recorded for moderator review. No email will be sent; "
            "keep the dispute reference for follow-up."
        ),
    )


# ── Awareness and public stats ────────────────────────────────────────────


@router.get("/awareness")
def awareness(db: Session = Depends(get_db)):
    with open(_DATA_DIR / "fraud_patterns.json", encoding="utf-8") as handle:
        patterns = json.load(handle).get("patterns", [])

    laws = db.query(Law).order_by(Law.id.asc()).all()
    return {
        "patterns": [
            {
                "id": item["id"],
                "name": item["name"],
                "risk_level": item.get("risk_level"),
                "short_desc": item.get("short_desc"),
                "full_desc": item.get("full_desc"),
                "how_it_happens": item.get("how_it_happens", []),
                "warning_signs": item.get("warning_signs", []),
                "immediate_action": item.get("immediate_action"),
                "prevention": item.get("prevention"),
            }
            for item in patterns
        ],
        "laws": [
            {"id": law.id, "act": law.act, "section": law.section, "summary": law.summary}
            for law in laws
        ],
        "helplines": helplines_for(db),
        "safety_note": "No report found does not mean an identifier is safe. Verify before paying.",
    }


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


@router.get("/stats")
def public_stats(db: Session = Depends(get_db)):
    """Aggregate counters only — never identifiers."""
    reports = db.query(Report).filter(Report.status == "verified").all()
    now = datetime.now(timezone.utc)
    month_counts: dict[str, int] = {}
    for report in reports:
        created = _as_utc(report.created_at)
        if created and created.year == now.year and created.month == now.month:
            month_counts[report.scam_type_code] = month_counts.get(report.scam_type_code, 0) + 1

    codes = sorted(month_counts, key=month_counts.get, reverse=True)[:5]
    types = {}
    if codes:
        types = {row.code: row.title for row in db.query(ScamType).filter(ScamType.code.in_(codes)).all()}

    return {
        "total_verified_reports": len(reports),
        "total_entities": db.query(Entity).count(),
        "total_reported_entities": db.query(Entity).filter(Entity.status == "reported").count(),
        "top_scam_types_this_month": [
            {"code": code, "title": types.get(code, code), "count": month_counts[code]}
            for code in codes
        ],
        "generated_at": now.isoformat(),
    }
