"""
backend/api/schemas.py  (v2 — beast mode)
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
import re


# ── Auth ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    password: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        cleaned = re.sub(r"[()\s\-]", "", v)
        if not re.match(r"^\+?\d{7,15}$", cleaned):
            raise ValueError("Invalid phone number")
        return cleaned

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Name too short")
        return v.strip()


class LoginRequest(BaseModel):
    identifier: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    full_name: str
    email: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Transaction — request ──────────────────────────────────────────────────

class TransactionRequest(BaseModel):
    amount: float
    platform: str
    tx_date: str
    tx_time: str
    # Behavioral context
    location_change: bool  = False
    new_recipient: bool    = True
    failed_attempts: int   = 0
    device_count: int      = 1
    txn_freq_1h: int       = 0
    txn_freq_24h: int      = 0
    # Behavioral stats (computed by frontend from history or defaulted)
    amount_z_score: float       = 0.0
    amount_vs_recent: float     = 0.0
    is_preferred_platform: bool = True

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        if v > 200000:
            raise ValueError("Exceeds UPI limit")
        return round(v, 2)

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v):
        if v not in {"Google Pay", "PhonePe", "Paytm", "BHIM"}:
            raise ValueError("Invalid platform")
        return v

    @field_validator("tx_date")
    @classmethod
    def validate_date(cls, v):
        if not re.match(r"^\d{2}/\d{2}/\d{4}$", v):
            raise ValueError("Date must be DD/MM/YYYY")
        return v

    @field_validator("tx_time")
    @classmethod
    def validate_time(cls, v):
        if not re.match(r"^\d{2}:\d{2}$", v):
            raise ValueError("Time must be HH:MM")
        return v


# ── Transaction — beast-mode response ─────────────────────────────────────

class AnomalyReason(BaseModel):
    factor: str
    detail: str


class FullFraudAnalysis(BaseModel):
    transaction_id: int
    amount: float
    platform: str

    # Core verdict
    is_fraud: bool
    fraud_score: float
    confidence_pct: float
    verdict: str           # SAFE | SUSPICIOUS | FRAUD
    risk_level: str        # LOW | MEDIUM | HIGH | CRITICAL

    # Behavioral intelligence
    behavior_flags: list[str]
    anomaly_reasons: list[AnomalyReason]
    feature_contributions: dict

    # Pattern matching
    matched_pattern_id: Optional[str]
    matched_pattern_name: Optional[str]
    pattern_similarity: float

    # Education & awareness
    fraud_how_it_works: Optional[str]
    fraud_warning_signs: list[str]
    immediate_action: Optional[str]
    prevention_tip: Optional[str]
    report_to: list[str]
    helplines: dict


class TransactionHistoryItem(BaseModel):
    id: int
    amount: float
    platform: str
    tx_date: str
    tx_time: str
    is_fraud: bool
    fraud_score: float
    verdict: str
    matched_pattern_id: Optional[str] = None
    matched_pattern_name: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class FraudStatsResponse(BaseModel):
    total_transactions: int
    fraud_count: int
    safe_count: int
    suspicious_count: int
    fraud_rate_pct: float
    total_amount_at_risk: float
    top_fraud_patterns: list[dict]
    recent_fraud_types: list[str]
