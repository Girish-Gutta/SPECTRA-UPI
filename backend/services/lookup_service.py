"""Assemble a public lookup result from stored data and local heuristics."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

try:  # pragma: no cover
    from ..db.models import Entity, Report, ScamType
    from .explain import build_explanation
    from .normalize import NormalizedValue, normalize
    from .patterns import all_local_signals
    from .verdict import Signal, compute_verdict
except (ImportError, ValueError):  # pragma: no cover
    from db.models import Entity, Report, ScamType
    from services.explain import build_explanation
    from services.normalize import NormalizedValue, normalize
    from services.patterns import all_local_signals
    from services.verdict import Signal, compute_verdict

DISCLAIMER = (
    "SPECTRA-UPI is a community reporting service, not a court, regulator or credit bureau. "
    "A report is one user's allegation and does not prove that a named person committed a crime. "
    "Always verify through official channels before paying."
)


def _model_signal(transaction: dict | None) -> float | None:
    """Run the existing XGBoost model only when transaction fields are given.

    The import is lazy and failures are swallowed so that public lookup keeps
    working on machines where the model artifacts or xgboost are unavailable.
    """
    if not transaction:
        return None
    try:  # pragma: no cover - depends on local model artifacts
        from ..api.predictor import predict
    except (ImportError, ValueError):
        try:  # pragma: no cover
            from api.predictor import predict
        except Exception:
            return None
    except Exception:
        return None

    try:  # pragma: no cover
        result = predict(
            amount=transaction.get("amount", 0),
            platform=transaction.get("platform", "Google Pay"),
            tx_date=transaction.get("tx_date", ""),
            tx_time=transaction.get("tx_time", ""),
            location_change=bool(transaction.get("location_change", False)),
            new_recipient=bool(transaction.get("new_recipient", True)),
            failed_attempts=int(transaction.get("failed_attempts", 0)),
            device_count=int(transaction.get("device_count", 1)),
            txn_freq_1h=int(transaction.get("txn_freq_1h", 0)),
            txn_freq_24h=int(transaction.get("txn_freq_24h", 0)),
            amount_z_score=float(transaction.get("amount_z_score", 0.0)),
            amount_vs_recent=float(transaction.get("amount_vs_recent", 0.0)),
            is_preferred_platform=bool(transaction.get("is_preferred_platform", True)),
        )
        return float(result.fraud_score)
    except Exception:
        return None


def _optional_link_signals(db: Session, value: NormalizedValue, entity_id: int | None) -> list[Signal]:
    """Optional external reputation checks. Missing keys simply return []."""
    try:
        from .linkcheck import check_url_signals
    except ImportError:  # pragma: no cover
        return []
    try:
        return check_url_signals(value, db=db, entity_id=entity_id)
    except Exception:  # pragma: no cover - never break lookup for an API outage
        return []


def perform_lookup(
    db: Session,
    query: str,
    requested_type: str = "auto",
    transaction: dict | None = None,
) -> dict:
    """Normalize, query, score and explain one identifier."""
    normalized = normalize(query, requested_type)
    entity = (
        db.query(Entity)
        .filter(Entity.type == normalized.type, Entity.value_hash == normalized.value_hash)
        .first()
    )

    reports: list[Report] = []
    if entity is not None:
        reports = (
            db.query(Report)
            .filter(Report.entity_id == entity.id)
            .order_by(Report.created_at.desc())
            .all()
        )

    verified = [r for r in reports if r.status == "verified"]
    pending = [r for r in reports if r.status == "pending"]
    total_loss = sum(float(r.amount_lost or 0) for r in verified)

    local = all_local_signals(normalized)
    local_signals = [
        Signal(
            code=item.code,
            source=item.source,
            severity=item.severity,
            label=item.label,
            detail=item.detail,
        )
        for item in local
    ]
    link_signals = _optional_link_signals(db, normalized, entity.id if entity else None)
    model_score = _model_signal(transaction)

    verdict = compute_verdict(
        verified_reports=len(verified),
        pending_reports=len(pending),
        local_signals=local_signals,
        link_signals=link_signals,
        model_score=model_score,
        total_reported_loss=total_loss,
    )

    explanation = build_explanation(db, reports, pending_count=len(pending))

    # Scam types actually involved in verified reports.
    codes: list[str] = []
    for report in verified:
        if report.scam_type_code not in codes:
            codes.append(report.scam_type_code)
    scam_types = []
    if codes:
        rows = db.query(ScamType).filter(ScamType.code.in_(codes)).all()
        by_code = {row.code: row for row in rows}
        for code in codes:
            row = by_code.get(code)
            if row is None:
                continue
            scam_types.append(
                {
                    "code": row.code,
                    "title": row.title,
                    "explanation": row.explanation,
                    "how_it_works": row.how_it_works,
                    "prevention_steps": row.prevention_steps or [],
                    "law_refs": row.law_refs or [],
                    "report_count": sum(1 for r in verified if r.scam_type_code == code),
                }
            )

    return {
        "query": {
            "input": query,
            "detected_type": normalized.type,
            "normalized_value": normalized.value,
            "masked_value": normalized.masked,
            "details": normalized.details,
        },
        "verdict": verdict.verdict,
        "verdict_label": verdict.label,
        "risk_level": verdict.risk_level,
        "signals": [
            {
                "code": sig.code,
                "source": sig.source,
                "severity": sig.severity,
                "label": sig.label,
                "detail": sig.detail,
            }
            for sig in verdict.signals
        ],
        "entity": {
            "found": entity is not None,
            "status": entity.status if entity else "clean",
            "first_seen": entity.first_seen if entity else None,
            "last_seen": entity.last_seen if entity else None,
        },
        "report_summary": {
            "verified_count": len(verified),
            "pending_count": len(pending),
            "total_count": len(reports),
            "total_reported_loss": round(total_loss, 2),
            "scam_type_counts": {item["code"]: item["report_count"] for item in scam_types},
        },
        "incident_summary": explanation.incident_summary,
        "why_risky": explanation.why_risky,
        "scam_types": scam_types,
        "laws": explanation.laws,
        "helplines": explanation.helplines,
        "prevention_steps": explanation.prevention_steps,
        "what_to_do": explanation.what_to_do,
        "timeline": [
            {
                **item,
                "date": item["date"].isoformat() if item["date"] else None,
            }
            for item in explanation.timeline
        ],
        "demo_data": explanation.demo_data,
        "safety_note": verdict.safety_note,
        "disclaimer": DISCLAIMER,
        "checked_at": datetime.utcnow().isoformat() + "Z",
    }
