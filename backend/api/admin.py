"""Moderator/admin endpoints for the moderation queue and disputes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

try:  # pragma: no cover
    from ..db import get_db
    from ..db.models import Dispute, ModerationLog, Report, ScamType
    from ..services.entity_service import recalculate_entity
    from ..services.normalize import mask_value
    from ..services.security import sanitize_text
    from .auth import require_roles
    from .admin_schemas import (
        AdminDisputeOut,
        AdminReportOut,
        AdminReportUpdated,
        DisputeAction,
        ModerationAction,
    )
except (ImportError, ValueError):  # pragma: no cover
    from db import get_db
    from db.models import Dispute, ModerationLog, Report, ScamType
    from services.entity_service import recalculate_entity
    from services.normalize import mask_value
    from services.security import sanitize_text
    from api.auth import require_roles
    from api.admin_schemas import (
        AdminDisputeOut,
        AdminReportOut,
        AdminReportUpdated,
        DisputeAction,
        ModerationAction,
    )

router = APIRouter(
    prefix="/admin",
    tags=["moderation"],
    dependencies=[Depends(require_roles("moderator", "admin"))],
)


def _report_out(report: Report) -> AdminReportOut:
    entity = report.entity
    return AdminReportOut(
        id=report.id,
        entity_id=report.entity_id,
        entity_type=entity.type,
        entity_value=entity.value,
        entity_masked=mask_value(entity.value, entity.type),
        entity_status=entity.status,
        scam_type_code=report.scam_type_code,
        scam_type_title=report.scam_type.title if report.scam_type else None,
        amount_lost=report.amount_lost,
        incident_date=report.incident_date,
        description=report.description,
        evidence_url=report.evidence_url,
        contact_email=report.contact_email,
        reporter_user_id=report.reporter_user_id,
        priority_flag=report.priority_flag,
        status=report.status,
        created_at=report.created_at,
        reviewed_by=report.reviewed_by,
        reviewed_at=report.reviewed_at,
    )


@router.get("/reports", response_model=list[AdminReportOut])
def list_reports(
    status: str = Query("pending", pattern="^(pending|verified|rejected|all)$"),
    priority: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Report)
    if status != "all":
        query = query.filter(Report.status == status)
    if priority is not None:
        query = query.filter(Report.priority_flag == priority)
    reports = (
        query.order_by(Report.priority_flag.desc(), Report.created_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [_report_out(report) for report in reports]


@router.patch("/reports/{report_id}", response_model=AdminReportUpdated)
def moderate_report(
    report_id: int,
    body: ModerationAction,
    db: Session = Depends(get_db),
    moderator=Depends(require_roles("moderator", "admin")),
):
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status == "verified" and body.action == "verify":
        raise HTTPException(status_code=409, detail="Report is already verified")
    if report.status == "rejected" and body.action == "reject":
        raise HTTPException(status_code=409, detail="Report is already rejected")

    report.status = "verified" if body.action == "verify" else "rejected"
    report.reviewed_by = moderator.id
    report.reviewed_at = datetime.now(timezone.utc)
    db.add(
        ModerationLog(
            report_id=report.id,
            action=report.status,
            reviewer_id=moderator.id,
            note=sanitize_text(body.note, 1000) or None,
            timestamp=datetime.now(timezone.utc),
        )
    )
    db.flush()
    recalculate_entity(db, report.entity)
    db.commit()
    db.refresh(report)
    db.refresh(report.entity)

    return AdminReportUpdated(
        id=report.id,
        status=report.status,
        entity_id=report.entity_id,
        entity_status=report.entity.status,
        verified_report_count=report.entity.verified_report_count,
        total_report_count=report.entity.total_report_count,
        message="Report verified. Only verified reports count toward HIGH RISK."
        if report.status == "verified"
        else "Report rejected. It no longer contributes to the public verdict.",
    )


@router.get("/disputes", response_model=list[AdminDisputeOut])
def list_disputes(
    status: str = Query("open", pattern="^(open|resolved|all)$"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Dispute)
    if status != "all":
        query = query.filter(Dispute.status == status)
    rows = query.order_by(Dispute.created_at.asc()).limit(limit).all()
    return [
        AdminDisputeOut(
            id=row.id,
            entity_id=row.entity_id,
            entity_value=row.entity.value,
            entity_masked=mask_value(row.entity.value, row.entity.type),
            contact_email=row.contact_email,
            reason=row.reason,
            status=row.status,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.patch("/disputes/{dispute_id}", response_model=AdminDisputeOut)
def resolve_dispute(
    dispute_id: int,
    body: DisputeAction,
    db: Session = Depends(get_db),
):
    dispute = db.get(Dispute, dispute_id)
    if dispute is None:
        raise HTTPException(status_code=404, detail="Dispute not found")
    dispute.status = body.status
    db.commit()
    db.refresh(dispute)
    return AdminDisputeOut(
        id=dispute.id,
        entity_id=dispute.entity_id,
        entity_value=dispute.entity.value,
        entity_masked=mask_value(dispute.entity.value, dispute.entity.type),
        contact_email=dispute.contact_email,
        reason=dispute.reason,
        status=dispute.status,
        created_at=dispute.created_at,
    )
