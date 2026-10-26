from services.verdict import (
    SAFETY_NOTE,
    VERDICT_HIGH,
    VERDICT_NONE,
    VERDICT_SUSPICIOUS,
    Signal,
    compute_verdict,
)


def test_verified_reports_produce_high_risk():
    result = compute_verdict(verified_reports=2, pending_reports=0, total_reported_loss=5000)
    assert result.verdict == VERDICT_HIGH
    assert result.label == "HIGH RISK / REPORTED"
    assert result.risk_level == "HIGH"


def test_many_verified_reports_are_critical():
    result = compute_verdict(verified_reports=5, pending_reports=3, total_reported_loss=1000)
    assert result.verdict == VERDICT_HIGH
    assert result.risk_level == "CRITICAL"


def test_pending_reports_never_create_high_risk():
    result = compute_verdict(verified_reports=0, pending_reports=50)
    assert result.verdict == VERDICT_SUSPICIOUS
    assert result.verdict != VERDICT_HIGH
    assert any(signal.code == "reports:pending" for signal in result.signals)


def test_no_reports_and_no_signals_is_no_reports_found():
    result = compute_verdict(verified_reports=0, pending_reports=0)
    assert result.verdict == VERDICT_NONE
    assert result.label == "NO REPORTS FOUND"
    assert result.safety_note == SAFETY_NOTE
    assert "does not guarantee safety" in result.safety_note


def test_local_risk_signal_makes_suspicious():
    signal = Signal(
        code="url:shortener",
        source="url",
        severity="medium",
        label="Shortened link",
        detail="Expand before opening.",
    )
    result = compute_verdict(verified_reports=0, pending_reports=0, local_signals=[signal])
    assert result.verdict == VERDICT_SUSPICIOUS


def test_low_signal_alone_stays_no_reports():
    signal = Signal(
        code="url:no-https",
        source="url",
        severity="low",
        label="Not https",
        detail="Prefer https.",
    )
    result = compute_verdict(verified_reports=0, pending_reports=0, local_signals=[signal])
    assert result.verdict == VERDICT_NONE


def test_model_signal_can_make_suspicious():
    result = compute_verdict(verified_reports=0, pending_reports=0, model_score=0.8)
    assert result.verdict == VERDICT_SUSPICIOUS
    assert any(signal.source == "model" for signal in result.signals)
