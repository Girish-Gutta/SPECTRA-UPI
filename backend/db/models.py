"""
backend/db/models.py
SQLAlchemy ORM models for SPECTRA-UPI.

Two generations of tables live here:

* ``users`` / ``transactions`` — the original authenticated transaction
  analyzer (kept unchanged so existing features keep working).
* The public scam-lookup tables (``entities``, ``reports``, ``scam_types``,
  ``laws``, ``helplines``, ``disputes``, ``moderation_log``,
  ``external_check_cache``, ``api_keys``).

The schema deliberately avoids PostgreSQL-only types so the same models work
on SQLite (local development) and PostgreSQL (free hosted tier).
"""

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    false,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def _utcnow() -> datetime:
    """Timezone-aware UTC timestamp used by every ``created_at`` column."""
    return datetime.now(timezone.utc)


# ── Original transaction-analyzer tables ──────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    # "user" | "moderator" | "admin". Existing rows are backfilled to "user"
    # by the startup migration.
    role = Column(
        String(16),
        nullable=False,
        default="user",
        server_default="user",
        index=True,
    )
    created_at = Column(DateTime, default=_utcnow)

    transactions = relationship("Transaction", back_populates="user", cascade="all, delete")

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Transaction fields (what the user submits)
    amount = Column(Float, nullable=False)
    platform = Column(String(50), nullable=False)
    tx_date = Column(String(20), nullable=False)  # DD/MM/YYYY
    tx_time = Column(String(10), nullable=False)  # HH:MM

    # ML feature inputs
    location_change = Column(Boolean, default=False)
    new_recipient = Column(Boolean, default=True)
    failed_attempts = Column(Integer, default=0)
    device_count = Column(Integer, default=1)

    # ML output
    is_fraud = Column(Boolean, nullable=False)
    fraud_score = Column(Float, nullable=False)
    matched_pattern_id = Column(String(10), nullable=True)
    matched_pattern_name = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction {self.id} ₹{self.amount} {'FRAUD' if self.is_fraud else 'SAFE'}>"


# ── Public scam-lookup tables ─────────────────────────────────────────────


class Entity(Base):
    """A normalized identifier that can be searched publicly."""

    __tablename__ = "entities"
    __table_args__ = (
        # The same normalized value can exist once per type (e.g. a phone
        # number and a UPI ID are different namespaces).
        UniqueConstraint("type", "value_hash", name="uq_entities_type_value_hash"),
        Index("ix_entities_type_status", "type", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(16), nullable=False, index=True)  # upi_id | url | qr_payload | phone
    value = Column(Text, nullable=False)                   # normalized value
    value_hash = Column(String(64), nullable=False, index=True)  # sha256 hex
    first_seen = Column(DateTime, nullable=False, default=_utcnow)
    last_seen = Column(DateTime, nullable=False, default=_utcnow)
    verified_report_count = Column(Integer, nullable=False, default=0, server_default="0")
    total_report_count = Column(Integer, nullable=False, default=0, server_default="0")
    status = Column(String(16), nullable=False, default="clean", server_default="clean", index=True)

    reports = relationship("Report", back_populates="entity", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Entity {self.type}:{self.value[:32]} ({self.status})>"


class ScamType(Base):
    """Seedable catalogue of UPI scam patterns (FP-001 … FP-008)."""

    __tablename__ = "scam_types"

    code = Column(String(20), primary_key=True)
    title = Column(String(120), nullable=False)
    explanation = Column(Text, nullable=True)
    how_it_works = Column(Text, nullable=True)
    prevention_steps = Column(JSON, nullable=False, default=list)
    law_refs = Column(JSON, nullable=False, default=list)  # list of Law.id values

    reports = relationship("Report", back_populates="scam_type")

    def __repr__(self) -> str:
        return f"<ScamType {self.code} {self.title}>"


class Law(Base):
    """Legal reference shown alongside a lookup result."""

    __tablename__ = "laws"

    id = Column(String(50), primary_key=True)
    act = Column(String(200), nullable=False)
    section = Column(String(50), nullable=False)
    summary = Column(Text, nullable=False)

    def __repr__(self) -> str:
        return f"<Law {self.act} s.{self.section}>"


class Helpline(Base):
    """Emergency / support contact shown to victims."""

    __tablename__ = "helplines"

    id = Column(String(50), primary_key=True)
    name = Column(String(150), nullable=False)
    number = Column(String(30), nullable=True)
    url = Column(String(2048), nullable=True)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, nullable=False, default=0, server_default="0")

    def __repr__(self) -> str:
        return f"<Helpline {self.name}>"


class Report(Base):
    """A user-submitted fraud report. Public detail only shows verified rows."""

    __tablename__ = "reports"
    __table_args__ = (
        Index("ix_reports_entity_status", "entity_id", "status"),
        Index("ix_reports_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(
        Integer,
        ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scam_type_code = Column(
        String(20),
        ForeignKey("scam_types.code"),
        nullable=False,
        index=True,
    )
    amount_lost = Column(Float, nullable=True)
    incident_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    evidence_url = Column(String(2048), nullable=True)
    reporter_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Salted hash — never a raw IP address.
    reporter_hash = Column(String(64), nullable=True, index=True)
    contact_email = Column(String(254), nullable=True)
    priority_flag = Column(Boolean, nullable=False, default=False, server_default=false())
    status = Column(String(16), nullable=False, default="pending", server_default="pending", index=True)
    # Indexed explicitly in __table_args__; do not also set index=True here or
    # SQLAlchemy will try to create the same index twice on a fresh database.
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    reviewed_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at = Column(DateTime, nullable=True)

    entity = relationship("Entity", back_populates="reports")
    scam_type = relationship("ScamType", back_populates="reports")
    reporter = relationship("User", foreign_keys=[reporter_user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    def __repr__(self) -> str:
        return f"<Report {self.id} entity={self.entity_id} {self.status}>"


class Dispute(Base):
    """Takedown / correction request for an entity listing."""

    __tablename__ = "disputes"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(
        Integer,
        ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contact_email = Column(String(254), nullable=True)
    reason = Column(Text, nullable=False)
    status = Column(String(16), nullable=False, default="open", server_default="open", index=True)
    created_at = Column(DateTime, nullable=False, default=_utcnow)

    entity = relationship("Entity")

    def __repr__(self) -> str:
        return f"<Dispute {self.id} entity={self.entity_id} {self.status}>"


class ModerationLog(Base):
    """Audit trail for verify/reject actions."""

    __tablename__ = "moderation_log"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(
        Integer,
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action = Column(String(32), nullable=False)  # verified | rejected | ...
    reviewer_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    note = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=_utcnow)

    report = relationship("Report")
    reviewer = relationship("User")

    def __repr__(self) -> str:
        return f"<ModerationLog report={self.report_id} {self.action}>"


class ExternalCheckCache(Base):
    """24-hour cache for optional external reputation lookups."""

    __tablename__ = "external_check_cache"
    __table_args__ = (
        Index("ix_external_cache_value_source", "value_hash", "source"),
    )

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(
        Integer,
        ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    value_hash = Column(String(64), nullable=True, index=True)
    source = Column(String(32), nullable=False, index=True)  # safe_browsing | virustotal | openphish | phishtank
    result_json = Column(JSON, nullable=False, default=dict)
    fetched_at = Column(DateTime, nullable=False, default=_utcnow, index=True)

    entity = relationship("Entity")

    def __repr__(self) -> str:
        return f"<ExternalCheckCache {self.source} {self.value_hash[:12] if self.value_hash else ''}>"


class ApiKey(Base):
    """Developer API keys. Only the hash is stored."""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    revoked = Column(Boolean, nullable=False, default=False, server_default=false())

    user = relationship("User")

    def __repr__(self) -> str:
        return f"<ApiKey {self.name} user={self.user_id}>"
