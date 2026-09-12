"""
backend/api/schemas.py
Pydantic models for request validation and response serialization
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
import re


# ── Auth Schemas ───────────────────────────────────────────────────────────

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
    identifier: str   # email or phone
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


# ── Transaction Schemas ────────────────────────────────────────────────────

class TransactionRequest(BaseModel):
    amount: float
    platform: str
    tx_date: str           # DD/MM/YYYY
    tx_time: str           # HH:MM
    location_change: bool = False
    new_recipient: bool   = True
    failed_attempts: int  = 0
    device_count: int     = 1

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        if v > 200000:
            raise ValueError("Amount exceeds UPI transaction limit")
        return round(v, 2)

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v):
        allowed = {"Google Pay", "PhonePe", "Paytm", "BHIM"}
        if v not in allowed:
            raise ValueError(f"Platform must be one of: {', '.join(allowed)}")
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
            raise ValueError("Time must be HH:MM (24-hour)")
        return v


class FraudPredictionResponse(BaseModel):
    transaction_id: int
    is_fraud: bool
    fraud_score: float          # 0.0–1.0
    confidence_pct: float       # human-readable percentage
    verdict: str                # "SAFE" | "SUSPICIOUS" | "FRAUD"
    top_risk_factors: list[str]
    amount: float
    platform: str


class TransactionHistoryItem(BaseModel):
    id: int
    amount: float
    platform: str
    tx_date: str
    tx_time: str
    is_fraud: bool
    fraud_score: float
    verdict: str
    created_at: datetime

    model_config = {"from_attributes": True}
