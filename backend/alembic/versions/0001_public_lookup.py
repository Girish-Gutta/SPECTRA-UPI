"""public scam lookup tables

Revision ID: 0001_public_lookup
Revises:
Create Date: 2026-10-26

This baseline migration is intentionally *additive and idempotent*:

* It never drops an existing table.
* It only creates the public-lookup tables that are missing, so it can be
  applied to an existing SPECTRA-UPI database that still only has
  ``users`` and ``transactions``.
* It works on SQLite and PostgreSQL (no Postgres-only types).
* ``downgrade`` is a no-op on purpose: removing these tables would destroy
  user-submitted reports and moderation history.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_public_lookup"
down_revision = None
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def _create_index_if_missing(name: str, table: str, columns: list[str], unique: bool = False) -> None:
    existing = {idx["name"] for idx in _inspector().get_indexes(table)}
    if name not in existing:
        op.create_index(name, table, columns, unique=unique)


def _create_table_if_missing(name: str, *columns, **kwargs) -> None:
    if not _inspector().has_table(name):
        op.create_table(name, *columns, **kwargs)


def upgrade() -> None:
    # ── baseline tables (fresh databases only) ────────────────────────────
    # A brand-new Postgres database needs these before the reports FK can be
    # created. Existing installations already have them and are left alone.
    _create_table_if_missing(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("full_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(120), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("hashed_password", sa.String(200), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("role", sa.String(16), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    _create_index_if_missing("ix_users_email", "users", ["email"], unique=True)
    _create_index_if_missing("ix_users_phone", "users", ["phone"], unique=True)
    _create_index_if_missing("ix_users_role", "users", ["role"])

    _create_table_if_missing(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("tx_date", sa.String(20), nullable=False),
        sa.Column("tx_time", sa.String(10), nullable=False),
        sa.Column("location_change", sa.Boolean(), nullable=True),
        sa.Column("new_recipient", sa.Boolean(), nullable=True),
        sa.Column("failed_attempts", sa.Integer(), nullable=True),
        sa.Column("device_count", sa.Integer(), nullable=True),
        sa.Column("is_fraud", sa.Boolean(), nullable=False),
        sa.Column("fraud_score", sa.Float(), nullable=False),
        sa.Column("matched_pattern_id", sa.String(10), nullable=True),
        sa.Column("matched_pattern_name", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ── users.role (existing installs) ────────────────────────────────────
    if _inspector().has_table("users"):
        user_columns = {c["name"] for c in _inspector().get_columns("users")}
        if "role" not in user_columns:
            op.add_column(
                "users",
                sa.Column("role", sa.String(16), nullable=False, server_default="user"),
            )
        _create_index_if_missing("ix_users_role", "users", ["role"])

    # ── entities ──────────────────────────────────────────────────────────
    _create_table_if_missing(
        "entities",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("value_hash", sa.String(64), nullable=False),
        sa.Column("first_seen", sa.DateTime(), nullable=False),
        sa.Column("last_seen", sa.DateTime(), nullable=False),
        sa.Column("verified_report_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_report_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False, server_default="clean"),
        sa.UniqueConstraint("type", "value_hash", name="uq_entities_type_value_hash"),
    )
    _create_index_if_missing("ix_entities_type", "entities", ["type"])
    _create_index_if_missing("ix_entities_value_hash", "entities", ["value_hash"])
    _create_index_if_missing("ix_entities_status", "entities", ["status"])
    _create_index_if_missing("ix_entities_type_status", "entities", ["type", "status"])

    # ── scam_types ────────────────────────────────────────────────────────
    _create_table_if_missing(
        "scam_types",
        sa.Column("code", sa.String(20), primary_key=True, nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("how_it_works", sa.Text(), nullable=True),
        sa.Column("prevention_steps", sa.JSON(), nullable=False),
        sa.Column("law_refs", sa.JSON(), nullable=False),
    )

    # ── laws ──────────────────────────────────────────────────────────────
    _create_table_if_missing(
        "laws",
        sa.Column("id", sa.String(50), primary_key=True, nullable=False),
        sa.Column("act", sa.String(200), nullable=False),
        sa.Column("section", sa.String(50), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
    )

    # ── helplines ─────────────────────────────────────────────────────────
    _create_table_if_missing(
        "helplines",
        sa.Column("id", sa.String(50), primary_key=True, nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("number", sa.String(30), nullable=True),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
    )

    # ── reports ───────────────────────────────────────────────────────────
    _create_table_if_missing(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "entity_id",
            sa.Integer(),
            sa.ForeignKey("entities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "scam_type_code",
            sa.String(20),
            sa.ForeignKey("scam_types.code"),
            nullable=False,
        ),
        sa.Column("amount_lost", sa.Float(), nullable=True),
        sa.Column("incident_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("evidence_url", sa.String(2048), nullable=True),
        sa.Column(
            "reporter_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reporter_hash", sa.String(64), nullable=True),
        sa.Column("contact_email", sa.String(254), nullable=True),
        sa.Column("priority_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column(
            "reviewed_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
    )
    _create_index_if_missing("ix_reports_entity_id", "reports", ["entity_id"])
    _create_index_if_missing("ix_reports_scam_type_code", "reports", ["scam_type_code"])
    _create_index_if_missing("ix_reports_reporter_user_id", "reports", ["reporter_user_id"])
    _create_index_if_missing("ix_reports_reporter_hash", "reports", ["reporter_hash"])
    _create_index_if_missing("ix_reports_status", "reports", ["status"])
    _create_index_if_missing("ix_reports_entity_status", "reports", ["entity_id", "status"])
    _create_index_if_missing("ix_reports_created_at", "reports", ["created_at"])

    # ── disputes ──────────────────────────────────────────────────────────
    _create_table_if_missing(
        "disputes",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "entity_id",
            sa.Integer(),
            sa.ForeignKey("entities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("contact_email", sa.String(254), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    _create_index_if_missing("ix_disputes_entity_id", "disputes", ["entity_id"])
    _create_index_if_missing("ix_disputes_status", "disputes", ["status"])

    # ── moderation_log ────────────────────────────────────────────────────
    _create_table_if_missing(
        "moderation_log",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "report_id",
            sa.Integer(),
            sa.ForeignKey("reports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column(
            "reviewer_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
    )
    _create_index_if_missing("ix_moderation_log_report_id", "moderation_log", ["report_id"])

    # ── external_check_cache ──────────────────────────────────────────────
    _create_table_if_missing(
        "external_check_cache",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "entity_id",
            sa.Integer(),
            sa.ForeignKey("entities.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("value_hash", sa.String(64), nullable=True),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
    )
    _create_index_if_missing("ix_external_check_cache_entity_id", "external_check_cache", ["entity_id"])
    _create_index_if_missing("ix_external_check_cache_value_hash", "external_check_cache", ["value_hash"])
    _create_index_if_missing("ix_external_check_cache_source", "external_check_cache", ["source"])
    _create_index_if_missing("ix_external_check_cache_fetched_at", "external_check_cache", ["fetched_at"])
    _create_index_if_missing(
        "ix_external_cache_value_source",
        "external_check_cache",
        ["value_hash", "source"],
    )

    # ── api_keys ──────────────────────────────────────────────────────────
    _create_table_if_missing(
        "api_keys",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("key_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    _create_index_if_missing("ix_api_keys_user_id", "api_keys", ["user_id"])
    _create_index_if_missing("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)


def downgrade() -> None:
    """No-op by design.

    Dropping these tables would permanently delete public reports, disputes
    and the moderation audit trail. Restore from a backup instead.
    """
    pass
