"""Shared entity helpers used by seeding, reporting and moderation."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from sqlalchemy.orm import Session

try:  # pragma: no cover - import shim for both package layouts
    from ..db.models import Entity, Report
except (ImportError, ValueError):  # pragma: no cover
    from db.models import Entity, Report


def value_hash(value: str) -> str:
    """Stable sha256 of an already-normalized value.

    The hash lets us index long URLs without putting them in a unique index
    (MySQL-style limits do not apply here, but hashes keep the index compact
    and avoid leaking values into logs).
    """
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def recalculate_entity(db: Session, entity: Entity) -> Entity:
    """Recompute cached report counters and public status from report rows.

    Only *verified* reports can make an entity ``reported``. Pending reports
    can raise it to ``suspicious`` but never beyond that.
    """
    reports = db.query(Report).filter(Report.entity_id == entity.id).all()
    verified = sum(1 for r in reports if r.status == "verified")
    pending = sum(1 for r in reports if r.status == "pending")

    entity.verified_report_count = verified
    entity.total_report_count = len(reports)
    if verified > 0:
        entity.status = "reported"
    elif pending > 0:
        entity.status = "suspicious"
    else:
        entity.status = "clean"

    entity.last_seen = datetime.now(timezone.utc)
    db.add(entity)
    return entity
