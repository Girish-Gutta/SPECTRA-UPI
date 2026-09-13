"""
backend/api/explainer.py
Beast-mode: matches transaction to known fraud patterns, builds human-readable explanation,
returns awareness info and action checklist.
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Load fraud patterns knowledge base once
_KB_PATH = Path(__file__).resolve().parent.parent / "data" / "fraud_patterns.json"
with open(_KB_PATH, encoding="utf-8") as f:
    _KB = json.load(f)

PATTERNS = {p["id"]: p for p in _KB["patterns"]}
HELPLINES = _KB["helplines"]


@dataclass
class ExplainedResult:
    is_fraud: bool
    fraud_score: float
    confidence_pct: float
    verdict: str                    # SAFE | SUSPICIOUS | FRAUD
    risk_level: str                 # LOW | MEDIUM | HIGH | CRITICAL

    # Behavioral explanation
    behavior_flags: list            # list of plain-English flags
    anomaly_reasons: list           # why this transaction is unusual

    # Pattern match
    matched_pattern_id: Optional[str]
    matched_pattern_name: Optional[str]
    pattern_similarity: float       # 0–1

    # Education
    fraud_how_it_works: Optional[str]
    fraud_warning_signs: list
    immediate_action: Optional[str]
    prevention_tip: Optional[str]
    report_to: list
    helplines: dict

    # Meta
    feature_contributions: dict     # feature → contribution weight


def _match_pattern(
    amount: float,
    new_recipient: bool,
    location_change: bool,
    failed_attempts: int,
    device_count: int,
    txn_freq_1h: int,
    amount_z_score: float,
) -> tuple[str, float]:
    """
    Score each of the 8 patterns against transaction characteristics.
    Returns (pattern_id, similarity_score).
    """
    scores = {}

    # FP-001 SIM Swap
    scores["FP-001"] = (
        (0.35 if device_count >= 3 else 0.0) +
        (0.30 if location_change else 0.0) +
        (0.20 if amount > 10000 else 0.0) +
        (0.15 if new_recipient else 0.0)
    )

    # FP-002 Fake Collect
    scores["FP-002"] = (
        (0.40 if new_recipient else 0.0) +
        (0.35 if amount_z_score > 1.5 else amount_z_score * 0.1 if amount_z_score > 0 else 0.0) +
        (0.25 if txn_freq_1h >= 2 else 0.0)
    )

    # FP-003 Fake QR
    scores["FP-003"] = (
        (0.45 if new_recipient else 0.0) +
        (0.35 if amount % 100 == 0 and 100 <= amount <= 10000 else 0.0) +
        (0.20 if 0 <= device_count <= 2 else 0.0)
    )

    # FP-004 OTP/Vishing
    scores["FP-004"] = (
        (0.40 if failed_attempts >= 1 else 0.0) +
        (0.30 if device_count >= 2 else 0.0) +
        (0.30 if new_recipient else 0.0)
    )

    # FP-005 OLX Marketplace
    scores["FP-005"] = (
        (0.40 if new_recipient else 0.0) +
        (0.35 if amount >= 5000 and amount % 1000 == 0 else 0.0) +
        (0.25 if failed_attempts == 0 else 0.0)
    )

    # FP-006 KYC Scam
    scores["FP-006"] = (
        (0.45 if failed_attempts >= 2 else 0.0) +
        (0.35 if device_count >= 2 else 0.0) +
        (0.20 if amount <= 100 else 0.0)
    )

    # FP-007 Advance Fee
    scores["FP-007"] = (
        (0.40 if amount <= 2000 else 0.0) +
        (0.40 if new_recipient else 0.0) +
        (0.20 if txn_freq_1h >= 1 else 0.0)
    )

    # FP-008 Remote Access
    scores["FP-008"] = (
        (0.40 if device_count >= 3 else 0.0) +
        (0.30 if location_change else 0.0) +
        (0.20 if amount > 10000 else 0.0) +
        (0.10 if txn_freq_1h >= 3 else 0.0)
    )

    best_id   = max(scores, key=scores.get)
    best_score = scores[best_id]
    return best_id, round(best_score, 3)


def _behavioral_flags(
    amount: float,
    amount_z_score: float,
    new_recipient: bool,
    failed_attempts: int,
    location_change: bool,
    device_count: int,
    txn_freq_1h: int,
    txn_freq_24h: int,
    amount_vs_recent: float,
    is_preferred_platform: bool,
    hour: int,
) -> list:
    flags = []

    if amount_z_score > 2.0:
        flags.append(f"Amount is {amount_z_score:.1f}x above your usual transaction size — highly unusual")
    elif amount_z_score > 1.0:
        flags.append(f"Amount is {amount_z_score:.1f}x above your typical transaction size")

    if amount_vs_recent > 3.0:
        flags.append(f"This is {amount_vs_recent:.0f}x your average transaction in the last 24 hours")

    if new_recipient:
        flags.append("Sending to a recipient you have never paid before")

    if failed_attempts >= 3:
        flags.append(f"{failed_attempts} failed attempts before this transaction — possible PIN guessing")
    elif failed_attempts >= 1:
        flags.append(f"{failed_attempts} failed attempt(s) before this transaction")

    if location_change:
        flags.append("Transaction initiated from an unusual or new location")

    if device_count >= 3:
        flags.append(f"{device_count} devices linked to your account — unusually high")
    elif device_count >= 2:
        flags.append("Multiple devices detected on your account")

    if txn_freq_1h >= 4:
        flags.append(f"{txn_freq_1h} transactions in the last hour — unusually high frequency")
    elif txn_freq_1h >= 2:
        flags.append(f"{txn_freq_1h} transactions in the last hour")

    if txn_freq_24h >= 10:
        flags.append(f"{txn_freq_24h} transactions today — above your usual daily activity")

    if not is_preferred_platform:
        flags.append("Transaction on a platform you rarely use")

    if hour < 5 or hour >= 23:
        flags.append(f"Transaction at {hour:02d}:xx — unusual hour for your activity")

    if amount > 50000:
        flags.append(f"Transaction amount ₹{amount:,.0f} exceeds 50% of the per-day UPI limit")

    return flags[:6]  # cap at 6 flags


def explain(
    amount: float,
    platform: str,
    hour: int,
    new_recipient: bool,
    location_change: bool,
    failed_attempts: int,
    device_count: int,
    txn_freq_1h: int,
    txn_freq_24h: int,
    amount_z_score: float,
    amount_vs_recent: float,
    is_preferred_platform: bool,
    fraud_score: float,
) -> ExplainedResult:

    # Verdict
    if fraud_score >= 0.65:
        verdict    = "FRAUD"
        risk_level = "CRITICAL" if fraud_score >= 0.85 else "HIGH"
    elif fraud_score >= 0.35:
        verdict    = "SUSPICIOUS"
        risk_level = "MEDIUM"
    else:
        verdict    = "SAFE"
        risk_level = "LOW"

    # Behavioral flags
    b_flags = _behavioral_flags(
        amount, amount_z_score, new_recipient, failed_attempts,
        location_change, device_count, txn_freq_1h, txn_freq_24h,
        amount_vs_recent, is_preferred_platform, hour
    )

    # Anomaly reasons (structured)
    anomaly = []
    if amount_z_score > 1.5:
        anomaly.append({"factor": "Amount", "detail": f"₹{amount:,.2f} is {amount_z_score:.1f} std deviations above your average"})
    if new_recipient:
        anomaly.append({"factor": "Recipient", "detail": "First-time recipient — no prior transaction history"})
    if failed_attempts >= 1:
        anomaly.append({"factor": "Auth Attempts", "detail": f"{failed_attempts} failed attempt(s) before success"})
    if location_change:
        anomaly.append({"factor": "Location", "detail": "Transaction from an unfamiliar location"})
    if device_count >= 3:
        anomaly.append({"factor": "Devices", "detail": f"{device_count} devices on account — possible account compromise"})
    if txn_freq_1h >= 3:
        anomaly.append({"factor": "Frequency", "detail": f"{txn_freq_1h} transactions in one hour is unusual"})

    # Pattern matching
    pat_id, pat_sim = _match_pattern(
        amount, new_recipient, location_change,
        failed_attempts, device_count, txn_freq_1h, amount_z_score
    )

    pat_data = PATTERNS.get(pat_id, {}) if pat_sim >= 0.35 else {}
    matched_id   = pat_id if pat_sim >= 0.35 else None
    matched_name = pat_data.get("name") if pat_data else None

    # Feature contributions (for display)
    contrib = {
        "Amount anomaly":     round(min(amount_z_score / 4, 1.0), 2),
        "New recipient":      1.0 if new_recipient else 0.0,
        "Failed attempts":    round(min(failed_attempts / 3, 1.0), 2),
        "Location change":    1.0 if location_change else 0.0,
        "Device count":       round(min((device_count - 1) / 3, 1.0), 2),
        "Transaction freq":   round(min(txn_freq_1h / 5, 1.0), 2),
    }

    return ExplainedResult(
        is_fraud=verdict in ("FRAUD", "SUSPICIOUS"),
        fraud_score=round(fraud_score, 4),
        confidence_pct=round(fraud_score * 100, 1),
        verdict=verdict,
        risk_level=risk_level,
        behavior_flags=b_flags,
        anomaly_reasons=anomaly,
        matched_pattern_id=matched_id,
        matched_pattern_name=matched_name,
        pattern_similarity=pat_sim,
        fraud_how_it_works=pat_data.get("full_desc") if pat_data else None,
        fraud_warning_signs=pat_data.get("warning_signs", []) if pat_data else [],
        immediate_action=pat_data.get("immediate_action") if pat_data else None,
        prevention_tip=pat_data.get("prevention") if pat_data else None,
        report_to=pat_data.get("report_to", []) if pat_data else [],
        helplines=HELPLINES,
        feature_contributions=contrib,
    )
