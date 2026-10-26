"""Three-outcome verdict logic for public scam lookup.

The public service never says "SAFE". The only outcomes are:

* ``HIGH_RISK``      — at least one *verified* report
* ``SUSPICIOUS``     — pending reports, pattern/model/link signals, or both
* ``NO_REPORTS``     — nothing in the database and no risk signal

Pending reports are deliberately capped at SUSPICIOUS. Only a moderator can
verify a report, and only verified reports can produce HIGH_RISK.
"""

from __future__ import annotations

from dataclasses import dataclass, field

VERDICT_HIGH = "HIGH_RISK"
VERDICT_SUSPICIOUS = "SUSPICIOUS"
VERDICT_NONE = "NO_REPORTS"

VERDICT_LABELS = {
    VERDICT_HIGH: "HIGH RISK / REPORTED",
    VERDICT_SUSPICIOUS: "SUSPICIOUS",
    VERDICT_NONE: "NO REPORTS FOUND",
}

SAFETY_NOTE = "This does not guarantee safety. Verify before paying."


@dataclass
class Signal:
    code: str
    source: str  # reports | pattern | url | link | model
    severity: str  # info | low | medium | high
    label: str
    detail: str


@dataclass
class Verdict:
    verdict: str
    label: str
    risk_level: str
    signals: list[Signal] = field(default_factory=list)
    safety_note: str = SAFETY_NOTE

    @property
    def is_high_risk(self) -> bool:
        return self.verdict == VERDICT_HIGH


def compute_verdict(
    *,
    verified_reports: int,
    pending_reports: int,
    local_signals: list[Signal] | None = None,
    link_signals: list[Signal] | None = None,
    model_score: float | None = None,
    total_reported_loss: float = 0.0,
) -> Verdict:
    """Combine report counts and optional risk signals into one verdict.

    ``verified_reports`` and ``pending_reports`` come from the database.
    ``local_signals`` are keyword/URL heuristics. ``link_signals`` come from
    optional external reputation services. ``model_score`` is the transaction
    model probability, only present when transaction fields were supplied.
    """
    signals: list[Signal] = []

    if verified_reports > 0:
        signals.append(
            Signal(
                code="reports:verified",
                source="reports",
                severity="high",
                label=f"Reported {verified_reports} time{'s' if verified_reports != 1 else ''} by users",
                detail=(
                    "These reports were manually reviewed and verified by a moderator. "
                    "A verified report is a user allegation, not a criminal finding."
                ),
            )
        )
        if total_reported_loss > 0:
            signals.append(
                Signal(
                    code="reports:loss",
                    source="reports",
                    severity="high",
                    label="Users reported losing money",
                    detail=f"Verified reports total roughly Rs {total_reported_loss:,.0f} in reported losses.",
                )
            )

    if pending_reports > 0:
        # Never enough for HIGH_RISK, but worth showing.
        signals.append(
            Signal(
                code="reports:pending",
                source="reports",
                severity="medium" if verified_reports == 0 else "low",
                label=f"{pending_reports} report{'s' if pending_reports != 1 else ''} awaiting review",
                detail="Pending reports are not published as fact and have not yet been checked by a moderator.",
            )
        )

    signals.extend(local_signals or [])
    signals.extend(link_signals or [])

    if model_score is not None and model_score >= 0.35:
        severity = "high" if model_score >= 0.65 else "medium"
        signals.append(
            Signal(
                code="model:risk",
                source="model",
                severity=severity,
                label=f"Transaction risk model scored {model_score * 100:.0f}%",
                detail=(
                    "The XGBoost model was trained on synthetic data. Use this as one signal, "
                    "not as proof that this identifier is fraudulent."
                ),
            )
        )

    if verified_reports > 0:
        risk = "CRITICAL" if (verified_reports >= 3 or total_reported_loss >= 50000) else "HIGH"
        return Verdict(
            verdict=VERDICT_HIGH,
            label=VERDICT_LABELS[VERDICT_HIGH],
            risk_level=risk,
            signals=signals,
        )

    risky_signal = any(sig.severity in {"medium", "high"} for sig in signals)
    if pending_reports > 0 or risky_signal:
        return Verdict(
            verdict=VERDICT_SUSPICIOUS,
            label=VERDICT_LABELS[VERDICT_SUSPICIOUS],
            risk_level="MEDIUM",
            signals=signals,
        )

    return Verdict(
        verdict=VERDICT_NONE,
        label=VERDICT_LABELS[VERDICT_NONE],
        risk_level="UNKNOWN",
        signals=signals,
    )
