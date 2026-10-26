"""Pydantic schemas for moderator/admin endpoints."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class AdminReportOut(BaseModel):
    id: int
    entity_id: int
    entity_type: str
    entity_value: str
    entity_masked: str
    entity_status: str
    scam_type_code: str
    scam_type_title: Optional[str] = None
    amount_lost: Optional[float] = None
    incident_date: Optional[date] = None
    description: Optional[str] = None
    evidence_url: Optional[str] = None
    contact_email: Optional[str] = None
    reporter_user_id: Optional[int] = None
    priority_flag: bool
    status: str
    created_at: datetime
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None


class ModerationAction(BaseModel):
    action: Literal["verify", "reject"]
    note: str = Field(default="", max_length=1000)

    @field_validator("note")
    @classmethod
    def clean_note(cls, value: str) -> str:
        return value.strip()


class AdminReportUpdated(BaseModel):
    id: int
    status: str
    entity_id: int
    entity_status: str
    verified_report_count: int
    total_report_count: int
    message: str


class AdminDisputeOut(BaseModel):
    id: int
    entity_id: int
    entity_value: str
    entity_masked: str
    contact_email: Optional[str] = None
    reason: str
    status: str
    created_at: datetime


class DisputeAction(BaseModel):
    status: Literal["open", "resolved"] = "resolved"


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return value.strip()


class ApiKeyOut(BaseModel):
    id: int
    name: str
    prefix: str
    created_at: datetime
    revoked: bool


class ApiKeyCreated(ApiKeyOut):
    key: str
    message: str
