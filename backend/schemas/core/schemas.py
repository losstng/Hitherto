"""
Hitherto — Core schema (PostgreSQL, SQLAlchemy 2.x)

Covers A) core:
  - core.asset
  - core.regime_state
  - core.playbook
  - core.policy_proposal
  - core.decision
  - core.portfolio_snapshot

Conventions:
  - BIGINT surrogate keys with Identity
  - timestamptz everywhere (timezone-aware)
  - JSONB for payloads
  - Minimal hot-path indexes
  - Partial unique index: exactly one active playbook

Usage:
  1) pip install sqlalchemy psycopg[binary]  # or psycopg2
  2) Set DATABASE_URL, then run this file to create the schema.

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Index,
    CheckConstraint,
    ForeignKey,
    text,
    true,
)
from sqlalchemy.dialects import postgresql as pg

# ---------- Dialect types ----------
JSONB = pg.JSONB
TIMESTAMPTZ = pg.TIMESTAMP(timezone=True)
REAL4 = pg.REAL

# ---------- Metadata ----------
metadata = MetaData()

# ---------- Enums ----------
regime_type = pg.ENUM(
    "BULL",
    "BEAR",
    "LOW_VOL",
    "HIGH_VOL",
    "CRISIS",
    "RECOVERY",
    "OTHER",
    name="regime_type",
)

proposal_status = pg.ENUM(
    "DRAFT", "UNDER_REVIEW", "APPROVED", "REJECTED", name="proposal_status"
)

# ---------- Tables (schema: core) ----------
# 5) core.asset
asset = Table(
    "asset",
    metadata,
    Column("id", sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column(
        "created_at", TIMESTAMPTZ, nullable=False, server_default=text("now()")
    ),
    Column("symbol", sa.Text, nullable=False, unique=True),
    Column("venue", sa.Text, nullable=False),
    Column("currency", sa.Text, nullable=False),
    Column(
        "lot_size", sa.Numeric(20, 6), nullable=False, server_default=text("1")
    ),
    schema="core",
)

# 1) core.regime_state
regime_state = Table(
    "regime_state",
    metadata,
    Column("id", sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column(
        "created_at", TIMESTAMPTZ, nullable=False, server_default=text("now()")
    ),
    Column("asof", TIMESTAMPTZ, nullable=False),
    Column("regime", regime_type, nullable=False),
    Column("confidence", REAL4, nullable=False),
    Column("hysteresis_lock_until", TIMESTAMPTZ),
    Column("source", sa.Text, nullable=False),  # e.g., "HMM", "Human"
    CheckConstraint(
        "confidence >= 0 AND confidence <= 1", name="ck_regime_confidence_0_1"
    ),
    schema="core",
)
Index(
    "ix_regime_state_asof_desc", regime_state.c.asof.desc(), schema="core"
)

# 2) core.playbook
playbook = Table(
    "playbook",
    metadata,
    Column("id", sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column(
        "created_at", TIMESTAMPTZ, nullable=False, server_default=text("now()")
    ),
    Column("version", sa.Integer, nullable=False),
    Column("is_active", sa.Boolean, nullable=False, server_default=text("false")),
    Column("valid_from", TIMESTAMPTZ),
    Column("valid_to", TIMESTAMPTZ),
    Column("name", sa.Text, nullable=False),
    Column("notes", sa.Text),
    Column("weights", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column(
        "thresholds", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    ),
    Column("tiers", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column("horizons", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    schema="core",
)
# Exactly one active playbook (partial unique index)
Index(
    "uq_playbook_one_active",
    playbook.c.is_active,
    unique=True,
    postgresql_where=(playbook.c.is_active == true()),
    schema="core",
)

# 3) core.policy_proposal
policy_proposal = Table(
    "policy_proposal",
    metadata,
    Column("id", sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column(
        "created_at", TIMESTAMPTZ, nullable=False, server_default=text("now()")
    ),
    Column("asof", TIMESTAMPTZ, nullable=False),
    Column(
        "regime_state_id",
        sa.BigInteger,
        ForeignKey("core.regime_state.id", ondelete="SET NULL"),
    ),
    Column(
        "playbook_id",
        sa.BigInteger,
        ForeignKey("core.playbook.id", ondelete="SET NULL"),
    ),
    Column(
        "status",
        proposal_status,
        nullable=False,
        server_default=text("'DRAFT'"),
    ),
    Column("targets", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column("rationale", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column("metrics", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    schema="core",
)
Index("ix_policy_proposal_asof", policy_proposal.c.asof, schema="core")

# 4) core.decision
decision = Table(
    "decision",
    metadata,
    Column("id", sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column(
        "created_at", TIMESTAMPTZ, nullable=False, server_default=text("now()")
    ),
    Column(
        "proposal_id",
        sa.BigInteger,
        ForeignKey("core.policy_proposal.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("asof", TIMESTAMPTZ, nullable=False),
    Column("decider", sa.Text, nullable=False),  # "AUTO|HUMAN|RISK-DOWNGRADE"
    Column("notes", sa.Text),
    Column("orders", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column(
        "constraints_checked",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    ),
    schema="core",
)

# 5) core.portfolio_snapshot
portfolio_snapshot = Table(
    "portfolio_snapshot",
    metadata,
    Column("id", sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column(
        "created_at", TIMESTAMPTZ, nullable=False, server_default=text("now()")
    ),
    Column("asof", TIMESTAMPTZ, nullable=False),
    Column("positions", JSONB, nullable=False),  # map: asset_id -> qty/meta
    Column("cash", sa.Numeric(20, 6), nullable=False, server_default=text("0")),
    Column("gross_exposure", sa.Numeric(20, 6)),
    Column("net_exposure", sa.Numeric(20, 6)),
    schema="core",
)


# ---------- Bootstrap ----------
def bootstrap_core_schema(database_url: str) -> None:
    """Creates schema 'core', enum types, and tables (idempotent)."""
    engine = sa.create_engine(database_url, future=True)
    with engine.begin() as conn:
        # Ensure schema exists
        conn.exec_driver_sql("CREATE SCHEMA IF NOT EXISTS core")

        # Create enum types first (safe if they already exist)
        for enum in (regime_type, proposal_status):
            enum.create(conn, checkfirst=True)

        # Create tables and indexes
        metadata.create_all(conn, checkfirst=True)


if __name__ == "__main__":
    # Example:
    # DATABASE_URL = "postgresql+psycopg://user:pass@localhost:5432/hitherto"
    # bootstrap_core_schema(DATABASE_URL)
    pass
