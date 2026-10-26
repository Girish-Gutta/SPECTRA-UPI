"""Pydantic schemas for public lookup and reporting endpoints."""

from __future__ import annotations

from datetime import date as Date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

EntityType = Literal["auto", "upi_id", "url", "qr_payload", "phone"]


class QueryInfo(BaseModel):
    input: str
    detected_type: str
    normalized_value: str
    masked_value: str
    details: dict = Field(default_factory=dict)


class SignalOut(BaseModel):
    code: str
    source: str
    severity: str
    label: str
    detail: str


class EntityInfo(BaseModel):
    found: bool
    status: str
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None


class ReportSummaryOut(BaseModel):
    verified_count: int
    pending_count: int
    total_count: int
    total_reported_loss: float
    scam_type_counts: dict[str, int] = Field(default_factory=dict)


class ScamTypeOut(BaseModel):
    code: str
    title: str
    explanation: Optional[str] = None
    how_it_works: Optional[str] = None
    prevention_steps: list[str] = Field(default_factory=list)
    law_refs: list[str] = Field(default_factory=list)
    report_count: int = 0


class LawOut(BaseModel):
    id: str
    act: str
    section: str
    summary: str


class HelplineOut(BaseModel):
    id: str
    name: str
    number: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None


class WhatToDoOut(BaseModel):
    not_paid: list[str]
    already_paid: list[str]


class TimelineItemOut(BaseModel):
    date: Optional[Date] = None
    scam_type_code: str
    scam_type_title: str
    amount_lost: Optional[float] = None
    is_demo: bool = False


class LookupResponse(BaseModel):
    query: QueryInfo
    verdict: str
    verdict_label: str
    risk_level: str
    signals: list[SignalOut]
    entity: EntityInfo
    report_summary: ReportSummaryOut
    incident_summary: str
    why_risky: list[str]
    scam_types: list[ScamTypeOut]
    laws: list[LawOut]
    helplines: list[HelplineOut]
    prevention_steps: list[str]
    what_to_do: WhatToDoOut
    timeline: list[TimelineItemOut]
    demo_data: bool
    safety_note: str
    disclaimer: str
    checked_at: str


# ── Reporting ─────────────────────────────────────────────────────────────


class ReportCreate(BaseModel):
    entity_value: str = Field(min_length=2, max_length=2048)
    entity_type: EntityType = "auto"
    scam_type_code: str = Field(min_length=1, max_length=20)
    amount_lost: Optional[float] = None
    incident_date: Optional[Date] = None
    description: str = Field(min_length=10, max_length=2000)
    evidence_url: Optional[str] = Field(default=None, max_length=2048)
    contact_email: Optional[str] = Field(default=None, max_length=254)
    captcha_token: Optional[str] = Field(default=None, max_length=4096)

    @field_validator("entity_value", "description")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("amount_lost")
    @classmethod
    def validate_amount(cls, value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        if value < 0 or value > 100_000_000:
            raise ValueError("Amount must be between 0 and 10 crore")
        return round(value, 2)

    @field_validator("contact_email")
    @classmethod
    def validate_email(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value.strip() == "":
            return None
        text = value.strip()
        if "@" not in text or len(text) > 254 or " " in text:
            raise ValueError("Invalid email address")
        return text


class ReportCreated(BaseModel):
    id: int
    status: str
    message: str
    masked_value: str


class DisputeCreate(BaseModel):
    entity_value: str = Field(min_length=2, max_length=2048)
    entity_type: EntityType = "auto"
    contact_email: Optional[str] = Field(default=None, max_length=254)
    reason: str = Field(min_length=20, max_length=2000)
    captcha_token: Optional[str] = Field(default=None, max_length=4096)

    @field_validator("reason", "entity_value")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("contact_email")
    @classmethod
    def validate_email(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value.strip() == "":
            return None
        text = value.strip()
        if "@" not in text or " " in text or len(text) > 254:
            raise ValueError("Invalid email address")
        return text


class DisputeCreated(BaseModel):
    id: int
    status: str
    message: str
