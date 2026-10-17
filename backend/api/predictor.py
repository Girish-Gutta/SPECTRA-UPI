"""
backend/api/predictor.py  (v2 — beast mode)
Loads v2 model, runs prediction, passes to explainer for full analysis.

Note: the StandardScaler is loaded from a plain JSON artifact (mean/scale)
and applied with NumPy. This keeps the runtime free of sklearn/scipy, which
can be blocked by OS application-control policies on some machines.
"""

import json
import joblib
import numpy as np
from pathlib import Path
from .explainer import explain, ExplainedResult

_BASE = Path(__file__).resolve().parent.parent / "models"


class NumPyScaler:
    """Drop-in replacement for sklearn.preprocessing.StandardScaler.transform."""

    def __init__(self, mean, scale):
        self.mean_ = np.asarray(mean, dtype=float)
        self.scale_ = np.asarray(scale, dtype=float)

    def transform(self, X):
        X = np.asarray(X, dtype=float)
        return (X - self.mean_) / self.scale_


def _load_scaler(base_name):
    with open(_BASE / f"{base_name}.json", encoding="utf-8") as f:
        data = json.load(f)
    return NumPyScaler(data["mean"], data["scale"])


# Load v2 artifacts (fall back to v1 if v2 not found)
try:
    _model    = joblib.load(_BASE / "fraud_model_v2.pkl")
    _scaler   = _load_scaler("scaler_v2")
    _features = joblib.load(_BASE / "feature_columns_v2.pkl")
    _version  = "v2"
except FileNotFoundError:
    _model    = joblib.load(_BASE / "fraud_model.pkl")
    _scaler   = _load_scaler("scaler")
    _features = joblib.load(_BASE / "feature_columns.pkl")
    _version  = "v1"


def _extract_features(
    amount: float,
    platform: str,
    tx_date: str,
    tx_time: str,
    location_change: bool,
    new_recipient: bool,
    failed_attempts: int,
    device_count: int,
    txn_freq_1h: int,
    txn_freq_24h: int,
    amount_z_score: float,
    amount_vs_recent: float,
    is_preferred_platform: bool,
) -> np.ndarray:
    try:
        from datetime import datetime
        dt = datetime.strptime(f"{tx_date} {tx_time}", "%d/%m/%Y %H:%M")
        hour        = dt.hour
        day_of_week = dt.weekday()
        is_weekend  = int(day_of_week >= 5)
    except ValueError:
        hour = 12; day_of_week = 0; is_weekend = 0

    platforms = ["BHIM", "Google Pay", "Paytm", "PhonePe"]
    plat_enc  = {f"plat_{p}": int(platform == p) for p in platforms}

    row = {
        "amount":                 amount,
        "hour":                   hour,
        "day_of_week":            day_of_week,
        "is_weekend":             is_weekend,
        "device_count":           device_count,
        "location_change":        int(location_change),
        "failed_attempts":        failed_attempts,
        "new_recipient":          int(new_recipient),
        "txn_freq_1h":            txn_freq_1h,
        "txn_freq_24h":           txn_freq_24h,
        "amount_z_score":         amount_z_score,
        "amount_vs_recent_ratio": amount_vs_recent,
        "is_preferred_platform":  int(is_preferred_platform),
        "amount_round":           int(amount % 100 == 0 and amount >= 1000),
        **plat_enc,
    }

    # Gracefully handle v1 model (fewer features)
    return np.array([[row.get(f, 0) for f in _features]])


def predict(
    amount: float,
    platform: str,
    tx_date: str,
    tx_time: str,
    location_change: bool  = False,
    new_recipient: bool    = True,
    failed_attempts: int   = 0,
    device_count: int      = 1,
    txn_freq_1h: int       = 0,
    txn_freq_24h: int      = 0,
    amount_z_score: float  = 0.0,
    amount_vs_recent: float = 0.0,
    is_preferred_platform: bool = True,
) -> ExplainedResult:

    try:
        from datetime import datetime
        dt = datetime.strptime(f"{tx_date} {tx_time}", "%d/%m/%Y %H:%M")
        hour = dt.hour
    except ValueError:
        hour = 12

    X = _extract_features(
        amount, platform, tx_date, tx_time,
        location_change, new_recipient, failed_attempts, device_count,
        txn_freq_1h, txn_freq_24h, amount_z_score, amount_vs_recent,
        is_preferred_platform,
    )
    X_sc = _scaler.transform(X)
    fraud_score = float(_model.predict_proba(X_sc)[0][1])

    return explain(
        amount=amount,
        platform=platform,
        hour=hour,
        new_recipient=new_recipient,
        location_change=location_change,
        failed_attempts=failed_attempts,
        device_count=device_count,
        txn_freq_1h=txn_freq_1h,
        txn_freq_24h=txn_freq_24h,
        amount_z_score=amount_z_score,
        amount_vs_recent=amount_vs_recent,
        is_preferred_platform=is_preferred_platform,
        fraud_score=fraud_score,
    )
