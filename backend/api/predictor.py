"""
backend/api/predictor.py
Loads the trained XGBoost model and exposes a predict() function for the API.
"""

import joblib
import numpy as np
from pathlib import Path
from typing import NamedTuple

# ── Load artifacts once at startup ────────────────────────────────────────
_BASE = Path(__file__).parent.parent / "models"

_model    = joblib.load(_BASE / "fraud_model.pkl")
_scaler   = joblib.load(_BASE / "scaler.pkl")
_features = joblib.load(_BASE / "feature_columns.pkl")   # ordered list of feature names

# Feature importance order (from training) — used to explain predictions
_FEATURE_LABELS = {
    "amount":           "Unusually high transaction amount",
    "new_recipient":    "Sending to a new/unknown recipient",
    "failed_attempts":  "Multiple failed attempts before this transaction",
    "location_change":  "Transaction from a different location",
    "device_count":     "Multiple devices linked to this account",
    "txn_freq_1h":      "High transaction frequency in last hour",
    "hour":             "Transaction at an unusual hour",
    "is_weekend":       "Weekend transaction pattern",
    "plat_BHIM":        "Platform: BHIM",
    "plat_Google Pay":  "Platform: Google Pay",
    "plat_Paytm":       "Platform: Paytm",
    "plat_PhonePe":     "Platform: PhonePe",
}


class PredictionResult(NamedTuple):
    is_fraud: bool
    fraud_score: float        # 0.0–1.0
    confidence_pct: float
    verdict: str              # SAFE | SUSPICIOUS | FRAUD
    top_risk_factors: list


def _extract_features(
    amount: float,
    platform: str,
    tx_date: str,    # DD/MM/YYYY
    tx_time: str,    # HH:MM
    location_change: bool,
    new_recipient: bool,
    failed_attempts: int,
    device_count: int,
) -> np.ndarray:
    """Convert raw inputs into the feature vector the model expects."""

    # Parse hour and day_of_week from date/time strings
    try:
        from datetime import datetime
        dt = datetime.strptime(f"{tx_date} {tx_time}", "%d/%m/%Y %H:%M")
        hour        = dt.hour
        day_of_week = dt.weekday()
        is_weekend  = int(day_of_week >= 5)
    except ValueError:
        hour = 12; day_of_week = 0; is_weekend = 0

    # One-hot encode platform
    platforms = ["BHIM", "Google Pay", "Paytm", "PhonePe"]
    plat_encoded = {f"plat_{p}": int(platform == p) for p in platforms}

    # Build row as ordered dict matching _features list
    row = {
        "amount":          amount,
        "hour":            hour,
        "day_of_week":     day_of_week,
        "is_weekend":      is_weekend,
        "device_count":    device_count,
        "location_change": int(location_change),
        "failed_attempts": failed_attempts,
        "new_recipient":   int(new_recipient),
        "txn_freq_1h":     0,   # Not collected in UI — default to 0
        **plat_encoded,
    }

    return np.array([[row[f] for f in _features]])


def predict(
    amount: float,
    platform: str,
    tx_date: str,
    tx_time: str,
    location_change: bool = False,
    new_recipient: bool   = True,
    failed_attempts: int  = 0,
    device_count: int     = 1,
) -> PredictionResult:
    """Run fraud prediction. Returns structured result."""

    X = _extract_features(
        amount, platform, tx_date, tx_time,
        location_change, new_recipient, failed_attempts, device_count
    )
    X_scaled = _scaler.transform(X)

    fraud_score   = float(_model.predict_proba(X_scaled)[0][1])
    is_fraud      = fraud_score >= 0.5
    confidence_pct = round(fraud_score * 100, 1)

    # Verdict thresholds
    if fraud_score < 0.35:
        verdict = "SAFE"
    elif fraud_score < 0.65:
        verdict = "SUSPICIOUS"
    else:
        verdict = "FRAUD"

    # Risk factors — explain why this was flagged
    risk_factors = []
    importances = _model.feature_importances_
    feat_scores = dict(zip(_features, importances))

    # Highlight features with high importance AND high value
    row_vals = {
        "amount":          amount,
        "new_recipient":   int(new_recipient),
        "failed_attempts": failed_attempts,
        "location_change": int(location_change),
        "device_count":    device_count,
    }

    # Simple heuristics to explain top risk factors
    if amount > 20000:
        risk_factors.append(_FEATURE_LABELS["amount"])
    if new_recipient:
        risk_factors.append(_FEATURE_LABELS["new_recipient"])
    if failed_attempts > 0:
        risk_factors.append(_FEATURE_LABELS["failed_attempts"])
    if location_change:
        risk_factors.append(_FEATURE_LABELS["location_change"])
    if device_count > 2:
        risk_factors.append(_FEATURE_LABELS["device_count"])

    # If nothing specific triggered, note the overall score
    if not risk_factors and is_fraud:
        risk_factors.append("Unusual transaction pattern detected by ML model")

    return PredictionResult(
        is_fraud=is_fraud,
        fraud_score=round(fraud_score, 4),
        confidence_pct=confidence_pct,
        verdict=verdict,
        top_risk_factors=risk_factors[:3],   # cap at 3
    )
