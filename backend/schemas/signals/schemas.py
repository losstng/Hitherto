"""
Hitherto — Signals schema (PostgreSQL, SQLAlchemy 2.x)

Covers B) signals:
  - signals.signal_definition
  - signals.signal_event

Conventions:
  - BIGINT surrogate keys with Identity
  - timestamptz everywhere (timezone-aware)
  - JSONB for payloads/config
  - Minimal indexes

Usage:
  1) pip install sqlalchemy psycopg[binary]  # or psycopg2
  2) Set DATABASE_URL, then run this file to create the schema.

"""

from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy import (
    MetaData, Table, Column, Index, ForeignKey, text
)
from sqlalchemy.dialects import postgresql as pg


# ---------- Dialect types ----------
JSONB = pg.JSONB
TIMESTAMPTZ = pg.TIMESTAMP(timezone=True)

# ---------- Metadata ----------
metadata = MetaData()

# ---------- Enums ----------
signal_type = pg.ENUM(
    'PRICE_SPIKE', 'VOLUME_SPIKE', 'SEC_FILING', 'OTHER',
    name='signal_type'
)

# ---------- Tables (schema: signals) ----------
signal_definition = Table(
    'signal_definition', metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('name', sa.Text, nullable=False, unique=True),
    Column('description', sa.Text),
    Column('config', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    schema='signals'
)

signal_event = Table(
    'signal_event', metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('asof', TIMESTAMPTZ, nullable=False),
    Column('type', signal_type, nullable=False),
    Column('definition_id', sa.BigInteger,
           ForeignKey('signals.signal_definition.id', ondelete='CASCADE'),
           nullable=False),
    Column('asset_id', sa.BigInteger,
           ForeignKey('core.asset.id', ondelete='SET NULL')),
    Column('payload', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column('source', sa.Text, nullable=False),
    schema='signals'
)
Index('ix_signal_event_asof', signal_event.c.asof, schema='signals')
Index('ix_signal_event_asset', signal_event.c.asset_id, schema='signals')


# ---------- Bootstrap ----------
def bootstrap_signals_schema(database_url: str) -> None:
    """
    Creates schema 'signals', enum types, and tables (idempotent).
    """
    engine = sa.create_engine(database_url, future=True)
    with engine.begin() as conn:
        conn.exec_driver_sql("CREATE SCHEMA IF NOT EXISTS signals")
        signal_type.create(conn, checkfirst=True)
        metadata.create_all(conn, checkfirst=True)


if __name__ == "__main__":
    # Example:
    # DATABASE_URL = "postgresql+psycopg://user:pass@localhost:5432/hitherto"
    # bootstrap_signals_schema(DATABASE_URL)
    pass
