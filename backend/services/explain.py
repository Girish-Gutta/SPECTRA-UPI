"""Template-based explanation engine.

Every sentence in this module is generated from stored data (reports, scam
types, laws and helplines). There is no LLM and no hand-written copy per
identifier, so two different entities always get different explanations.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime

from sqlalchemy.orm import Session

try:  # pragma: no cover
    from ..db.models import Helpline, Law, Report, ScamType
except (ImportError, ValueError):  # pragma: no cover
    from db.models import Helpline, Law, Report, ScamType

GENERIC_NOT_PAID = [
    "Do not pay, approve a collect request, or share an OTP/PIN. You only enter a UPI PIN to send money, never to receive it.",
    "Check the recipient name shown inside your UPI app before confirming. A familiar logo or screenshot is not proof.",
    "If a caller claims to be from a bank, NPCI or the government, hang up and call the number printed on your card or app.",
    "Report the identifier here and at cybercrime.gov.in. Call 1930 if money has already moved.",
]

GENERIC_ALREADY_PAID = [
    "Call your bank or UPI app immediately and ask them to block the account and freeze/dispute the transaction.",
    "Call the National Cyber Crime Helpline 1930 and note the complaint number.",
    "File a complaint at cybercrime.gov.in with the transaction ID, amount and timestamp.",
    "Keep screenshots, SMS alerts and the UPI reference number. Do not delete the chat or payment record.",
    "Do not pay anyone who promises to 'recover' your money. Recovery-fee offers are a second scam.",
]


@dataclass
class Explanation:
    incident_summary: str
    why_risky: list[str] = field(default_factory=list)
    laws: list[dict] = field(default_factory=list)
    helplines: list[dict] = field(default_factory=list)
    prevention_steps: list[str] = field(default_factory=list)
    what_to_do: dict = field(default_factory=dict)
    timeline: list[dict] = field(default_factory=list)
    demo_data: bool = False


def _month_year(value: datetime | date | None) -> str:
    if value is None:
        return "an unknown date"
    if isinstance(value, datetime):
        value = value.date()
    return value.strftime("%B %Y")


def _date_range(dates: list[date]) -> str:
    if not dates:
        return "an unknown period"
    first, last = min(dates), max(dates)
    if first.year == last.year and first.month == last.month:
        return f"in {_month_year(first)}"
    return f"between {_month_year(first)} and {_month_year(last)}"


def _plural(count: int, singular: str) -> str:
    return singular if count == 1 else singular + "s"


def build_incident_summary(reports: list[Report], scam_types: dict[str, ScamType], pending_count: int = 0) -> str:
    """Create the 'Reported N times between …' paragraph."""
    verified = [r for r in reports if r.status == "verified"]
    if not verified:
        if pending_count:
            return (
                f"{pending_count} {_plural(pending_count, 'report')} "
                f"{'is' if pending_count == 1 else 'are'} awaiting moderator review. "
                "Pending reports are not published as fact."
            )
        return "No fraud reports have been recorded for this identifier in our database."

    dates = [r.incident_date for r in verified if r.incident_date]
    if not dates:
        dates = [r.created_at.date() for r in verified if r.created_at]

    counts = Counter(r.scam_type_code for r in verified)
    parts = []
    for code, count in counts.most_common():
        title = scam_types[code].title if code in scam_types else code
        parts.append(f"{count} {_plural(count, 'report')} of {title}")

    total_loss = sum(float(r.amount_lost or 0) for r in verified)
    sentence = (
        f"Reported {len(verified)} {_plural(len(verified), 'time')} "
        f"{_date_range(dates)}: {', '.join(parts)}."
    )
    if total_loss > 0:
        sentence += f" Total reported loss: Rs {total_loss:,.0f}."
    if any((r.description or "").startswith("[DEMO DATA]") for r in verified):
        sentence += " Some or all of these reports are clearly-labelled demo data."
    return sentence


def why_risky(scam_type_rows: list[ScamType]) -> list[str]:
    """Explain risk using only the scam types actually reported here."""
    output: list[str] = []
    for row in scam_type_rows:
        text = (row.explanation or "").strip()
        if not text:
            text = f"This identifier was reported in connection with {row.title.lower()}."
        output.append(f"{row.title}: {text}")
    return output


def laws_for(db: Session, scam_type_rows: list[ScamType]) -> list[dict]:
    ids: list[str] = []
    for row in scam_type_rows:
        for law_id in (row.law_refs or []):
            if law_id not in ids:
                ids.append(law_id)
    if not ids:
        return []
    rows = db.query(Law).filter(Law.id.in_(ids)).all()
    order = {law_id: index for index, law_id in enumerate(ids)}
    rows.sort(key=lambda law: order.get(law.id, 999))
    return [
        {"id": law.id, "act": law.act, "section": law.section, "summary": law.summary}
        for law in rows
    ]


def helplines_for(db: Session) -> list[dict]:
    rows = db.query(Helpline).order_by(Helpline.display_order.asc()).all()
    return [
        {
            "id": row.id,
            "name": row.name,
            "number": row.number,
            "url": row.url,
            "description": row.description,
        }
        for row in rows
    ]


def prevention_for(scam_type_rows: list[ScamType]) -> list[str]:
    steps: list[str] = []
    for row in scam_type_rows:
        for step in (row.prevention_steps or []):
            if step and step not in steps:
                steps.append(step)
    if not steps:
        steps = [GENERIC_NOT_PAID[0], GENERIC_NOT_PAID[1], GENERIC_NOT_PAID[2]]
    return steps[:8]


def timeline_for(reports: list[Report], scam_types: dict[str, ScamType]) -> list[dict]:
    """Verified reports in date order. No reporter identity is included."""
    verified = [r for r in reports if r.status == "verified"]
    verified.sort(key=lambda r: (r.incident_date or (r.created_at.date() if r.created_at else date.min)))
    items = []
    for report in verified:
        scam_type = scam_types.get(report.scam_type_code)
        items.append(
            {
                "date": (report.incident_date or (report.created_at.date() if report.created_at else None)),
                "scam_type_code": report.scam_type_code,
                "scam_type_title": scam_type.title if scam_type else report.scam_type_code,
                "amount_lost": report.amount_lost,
                "is_demo": (report.description or "").startswith("[DEMO DATA]"),
            }
        )
    return items


def build_explanation(db: Session, reports: list[Report], pending_count: int = 0) -> Explanation:
    """Build every public explanation section for one entity."""
    codes = []
    for report in reports:
        if report.status == "verified" and report.scam_type_code not in codes:
            codes.append(report.scam_type_code)

    scam_type_rows: list[ScamType] = []
    scam_type_map: dict[str, ScamType] = {}
    if codes:
        rows = db.query(ScamType).filter(ScamType.code.in_(codes)).all()
        scam_type_map = {row.code: row for row in rows}
        scam_type_rows = [scam_type_map[code] for code in codes if code in scam_type_map]

    demo_data = any(
        (r.description or "").startswith("[DEMO DATA]") for r in reports if r.status == "verified"
    )

    return Explanation(
        incident_summary=build_incident_summary(reports, scam_type_map, pending_count),
        why_risky=why_risky(scam_type_rows),
        laws=laws_for(db, scam_type_rows),
        helplines=helplines_for(db),
        prevention_steps=prevention_for(scam_type_rows),
        what_to_do={
            "not_paid": GENERIC_NOT_PAID,
            "already_paid": GENERIC_ALREADY_PAID,
        },
        timeline=timeline_for(reports, scam_type_map),
        demo_data=demo_data,
    )
