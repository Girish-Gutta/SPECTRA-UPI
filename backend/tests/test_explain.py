from datetime import date, datetime, timedelta, timezone

from db.models import Entity, Report
from services.entity_service import recalculate_entity, value_hash
from services.explain import build_explanation


def _add_entity(db, value, reports):
    entity = Entity(type="upi_id", value=value, value_hash=value_hash(value))
    db.add(entity)
    db.flush()
    for code, amount, description in reports:
        db.add(
            Report(
                entity_id=entity.id,
                scam_type_code=code,
                amount_lost=amount,
                incident_date=date.today() - timedelta(days=3),
                description=description,
                status="verified",
                created_at=datetime.now(timezone.utc),
            )
        )
    db.flush()
    recalculate_entity(db, entity)
    db.flush()
    return entity


def test_explanations_differ_between_entities(db_session):
    db = db_session
    first = _add_entity(
        db,
        "kyc-scam@exampleupi",
        [("FP-006", 1000, "Called about KYC expiry and sent a link.")],
    )
    second = _add_entity(
        db,
        "collect-scam@exampleupi",
        [("FP-002", 5000, "Sent a fake collect request for a refund.")],
    )
    db.commit()

    reports_a = db.query(Report).filter(Report.entity_id == first.id).all()
    reports_b = db.query(Report).filter(Report.entity_id == second.id).all()
    text_a = build_explanation(db, reports_a)
    text_b = build_explanation(db, reports_b)

    assert text_a.incident_summary != text_b.incident_summary
    assert "KYC" in text_a.why_risky[0]
    assert "Collect" in text_b.why_risky[0]
    assert text_a.laws != text_b.laws
    assert text_a.timeline[0]["scam_type_code"] == "FP-006"
    assert text_b.timeline[0]["scam_type_code"] == "FP-002"


def test_explanation_contains_both_payment_states(db_session):
    explanation = build_explanation(db_session, [], pending_count=1)
    assert "awaiting moderator review" in explanation.incident_summary
    assert explanation.what_to_do["not_paid"]
    assert explanation.what_to_do["already_paid"]
    assert any("1930" in step for step in explanation.what_to_do["already_paid"])
