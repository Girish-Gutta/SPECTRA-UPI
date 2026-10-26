"""Idempotent reference-data and demo-data seeding.

Everything here is safe to run on every startup:

* ``scam_types`` is refreshed from ``data/fraud_patterns.json``.
* ``laws`` and ``helplines`` are refreshed from ``data/reference.json``.
* Demo reports are inserted once and always carry a ``[DEMO DATA]`` prefix.

No seed operation ever deletes a user, transaction, report or entity.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:  # pragma: no cover - import shim for both package layouts
    from ..db.models import Entity, Helpline, Law, Report, ScamType
    from ..db.database import SessionLocal
    from .entity_service import recalculate_entity, value_hash
except (ImportError, ValueError):  # pragma: no cover
    from db.models import Entity, Helpline, Law, Report, ScamType
    from db.database import SessionLocal
    from services.entity_service import recalculate_entity, value_hash

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_json(name: str) -> dict:
    with open(_DATA_DIR / name, encoding="utf-8") as handle:
        return json.load(handle)


def _seed_scam_types(db, patterns: dict, reference: dict) -> None:
    law_refs = reference.get("scam_type_law_refs", {})
    for pattern in patterns.get("patterns", []):
        code = pattern["id"]
        row = db.get(ScamType, code)
        if row is None:
            row = ScamType(code=code)
            db.add(row)
        row.title = pattern["name"]
        row.explanation = pattern.get("full_desc") or pattern.get("short_desc")
        row.how_it_works = "\n".join(pattern.get("how_it_happens", []))
        # Prevention steps are template-driven; keep the concrete advice plus
        # the warning signs so the public page never needs hand-written copy.
        steps = []
        if pattern.get("prevention"):
            steps.append(pattern["prevention"])
        steps.extend(pattern.get("warning_signs", [])[:3])
        row.prevention_steps = steps
        row.law_refs = law_refs.get(code, [])
    db.flush()


def _seed_laws(db, reference: dict) -> None:
    for item in reference.get("laws", []):
        row = db.get(Law, item["id"])
        if row is None:
            row = Law(id=item["id"])
            db.add(row)
        row.act = item["act"]
        row.section = item["section"]
        row.summary = item["summary"]
    db.flush()


def _seed_helplines(db, reference: dict) -> None:
    for item in reference.get("helplines", []):
        row = db.get(Helpline, item["id"])
        if row is None:
            row = Helpline(id=item["id"])
            db.add(row)
        row.name = item["name"]
        row.number = item.get("number")
        row.url = item.get("url")
        row.description = item.get("description")
        row.display_order = item.get("display_order", 0)
    db.flush()


# ── Demo data ─────────────────────────────────────────────────────────────
# These identifiers use the reserved ``.example`` namespace and fictional
# handles. Every description starts with "[DEMO DATA]" so the API and UI can
# label it clearly. They must never be presented as real reports.

_DEMO_ENTITIES = [
    {
        "type": "upi_id",
        "value": "demo.kyc-alert@exampleupi",
        "reports": [
            ("FP-006", 1500.0, 21, "Kept calling as a bank officer about KYC expiry."),
            ("FP-006", 2200.0, 15, "Sent a fake KYC link and asked for a test payment."),
            ("FP-004", 900.0, 8, "Asked for an OTP to 'complete verification'."),
        ],
    },
    {
        "type": "url",
        "value": "https://demo-scam.example/kyc-verify",
        "reports": [
            ("FP-006", 0.0, 11, "Fake bank KYC page that asks for UPI PIN."),
        ],
    },
    {
        "type": "upi_id",
        "value": "demo.collect@exampleupi",
        "reports": [
            ("FP-002", 0.0, 3, "Sent a collect request while pretending to be a buyer."),
        ],
        "status_override": "pending",
    },
    {
        "type": "qr_payload",
        "value": "upi://pay?pa=demo.qr@exampleupi&pn=Demo%20Store",
        "reports": [],
    },
]


def _seed_demo_data(db) -> None:
    if os.getenv("DEMO_DATA_ENABLED", "true").lower() in {"0", "false", "no"}:
        return

    now = datetime.now(timezone.utc)
    for spec in _DEMO_ENTITIES:
        value = spec["value"]
        entity = (
            db.query(Entity)
            .filter(Entity.type == spec["type"], Entity.value_hash == value_hash(value))
            .first()
        )
        if entity is None:
            entity = Entity(
                type=spec["type"],
                value=value,
                value_hash=value_hash(value),
                first_seen=now - timedelta(days=30),
                last_seen=now,
            )
            db.add(entity)
            db.flush()

        demo_prefix = "[DEMO DATA] "
        existing = (
            db.query(Report)
            .filter(Report.entity_id == entity.id, Report.description.like(demo_prefix + "%"))
            .count()
        )
        if existing:
            recalculate_entity(db, entity)
            continue

        for scam_code, amount, days_ago, note in spec["reports"]:
            report_status = spec.get("status_override", "verified")
            created = now - timedelta(days=days_ago)
            db.add(
                Report(
                    entity_id=entity.id,
                    scam_type_code=scam_code,
                    amount_lost=amount or None,
                    incident_date=(now - timedelta(days=days_ago + 7)).date(),
                    description=demo_prefix + note,
                    evidence_url=None,
                    reporter_user_id=None,
                    reporter_hash=None,
                    contact_email=None,
                    priority_flag=False,
                    status=report_status,
                    created_at=created,
                    reviewed_at=created if report_status == "verified" else None,
                )
            )
        # SessionLocal disables autoflush, so push the new reports before
        # recalculating the cached counters.
        db.flush()
        recalculate_entity(db, entity)


def seed_all() -> None:
    """Seed reference data and clearly-labelled demo rows."""
    patterns = _load_json("fraud_patterns.json")
    reference = _load_json("reference.json")

    db = SessionLocal()
    try:
        _seed_laws(db, reference)
        _seed_helplines(db, reference)
        _seed_scam_types(db, patterns, reference)
        _seed_demo_data(db)
        db.commit()
        print("[SEED] reference data and demo rows ready")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
