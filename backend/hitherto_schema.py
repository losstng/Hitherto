from __future__ import annotations

import datetime as _dt

import sqlalchemy as sa
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    ForeignKey,
    Index,
    UniqueConstraint,
    CheckConstraint,
    PrimaryKeyConstraint,
    text,
    true,
)
from sqlalchemy.dialects import postgresql as pg

# ---------- Dialect helpers ----------
JSONB = pg.JSONB
TIMESTAMPTZ = pg.TIMESTAMP(timezone=True)
INTERVAL = pg.INTERVAL
REAL4 = pg.REAL
DOUBLE = pg.DOUBLE_PRECISION
DATERANGE = pg.DATERANGE

# ---------- Global metadata ----------
metadata = MetaData()

# ---------- Enums ----------
regime_type = pg.ENUM(
    'BULL',
    'BEAR',
    'LOW_VOL',
    'HIGH_VOL',
    'CRISIS',
    'RECOVERY',
    'OTHER',
    name='regime_type',
)

verdict_status = pg.ENUM(
    'APPROVED',
    'DOWNGRADED',
    'REJECTED',
    'TIGHTEN',
    name='verdict_status',
)

proposal_status = pg.ENUM(
    'DRAFT',
    'UNDER_REVIEW',
    'APPROVED',
    'REJECTED',
    name='proposal_status',
)

human_action = pg.ENUM(
    'APPROVE',
    'REJECT',
    'MODIFY',
    'ASK_RISK',
    name='human_action',
)

limit_kind = pg.ENUM(
    'GROSS_EXPOSURE',
    'NET_EXPOSURE',
    'ASSET',
    'SECTOR',
    'EXPOSURE',
    'VAR',
    'ES',
    'DRAWDOWN',
    'TURNOVER',
    'LEVERAGE',
    'LIQUIDITY',
    name='limit_kind',
)

# =========================
# A) core schema
# =========================

# 5) core.asset
core_asset = Table(
    'asset',
    metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('symbol', sa.Text, nullable=False, unique=True),
    Column('venue', sa.Text, nullable=False),
    Column('currency', sa.Text, nullable=False),
    Column('lot_size', sa.Numeric(20, 6), nullable=False, server_default=text('1')),
    schema='core',
)

# 1) core.regime_state
core_regime_state = Table(
    'regime_state',
    metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('asof', TIMESTAMPTZ, nullable=False),
    Column('session_date', sa.Date),
    Column('session_id', sa.Text),
    Column('regime', regime_type, nullable=False),
    Column('confidence', REAL4, nullable=False),
    Column('hysteresis_lock_until', TIMESTAMPTZ),
    Column('source', sa.Text, nullable=False),
    CheckConstraint('confidence >= 0 AND confidence <= 1', name='ck_regime_confidence_0_1'),
    schema='core',
)

Index('ix_regime_state_asof', core_regime_state.c.asof)
Index(
    'ix_regime_state_asof_recent',
    core_regime_state.c.asof,
    postgresql_where=core_regime_state.c.asof > text("now() - interval '180 days'"),
)

# 2) core.playbook
core_playbook = Table(
    'playbook',
    metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('version', sa.Integer, nullable=False),
    Column('is_active', sa.Boolean, nullable=False, server_default=text('false')),
    Column('valid_from', TIMESTAMPTZ),
    Column('valid_to', TIMESTAMPTZ),
    Column('name', sa.Text, nullable=False),
    Column('notes', sa.Text),
    Column('weights', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column('thresholds', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column('tiers', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column('horizons', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    schema='core',
)

Index(
    'uq_playbook_one_active',
    core_playbook.c.is_active,
    unique=True,
    postgresql_where=(core_playbook.c.is_active == true()),
)

# 3) core.policy_proposal
core_policy_proposal = Table(
    'policy_proposal',
    metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('asof', TIMESTAMPTZ, nullable=False),
    Column('session_date', sa.Date),
    Column('session_id', sa.Text),
    Column('regime_state_id', sa.BigInteger, ForeignKey('core.regime_state.id', ondelete='SET NULL')),
    Column('playbook_id', sa.BigInteger, ForeignKey('core.playbook.id', ondelete='SET NULL')),
    Column('status', proposal_status, nullable=False, server_default=text("'DRAFT'")),
    Column('targets', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column('rationale', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column('metrics', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    schema='core',
)

Index('ix_policy_proposal_asof', core_policy_proposal.c.asof)

# 4) core.decision
core_decision = Table(
    'decision',
    metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('proposal_id', sa.BigInteger, ForeignKey('core.policy_proposal.id', ondelete='CASCADE'), nullable=False),
    Column('asof', TIMESTAMPTZ, nullable=False),
    Column('decider', sa.Text, nullable=False),
    Column('notes', sa.Text),
    Column('orders', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column('constraints_checked', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    schema='core',
)

# 5) core.portfolio_snapshot
core_portfolio_snapshot = Table(
    'portfolio_snapshot',
    metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('asof', TIMESTAMPTZ, nullable=False),
    Column('positions', JSONB, nullable=False),
    Column('cash', sa.Numeric(20, 6), nullable=False, server_default=text('0')),
    Column('gross_exposure', sa.Numeric(20, 6)),
    Column('net_exposure', sa.Numeric(20, 6)),
    schema='core',
)

# =========================
# B) signals schema
# =========================

# 6) signals.module
signals_module = Table(
    'module',
    metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('name', sa.Text, nullable=False, unique=True),
    Column('family', sa.Text, nullable=False),
    Column('owner', sa.Text),
    Column('is_active', sa.Boolean, nullable=False, server_default=text('true')),
    Column('expected_horizon', INTERVAL),
    schema='signals',
)

# 8) signals.fusion_trace
signals_fusion_trace = Table(
    'fusion_trace',
    metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('proposal_id', sa.BigInteger, ForeignKey('core.policy_proposal.id', ondelete='CASCADE'), nullable=False),
    Column('module_id', sa.BigInteger, ForeignKey('signals.module.id', ondelete='CASCADE'), nullable=False),
    Column('weight', REAL4),
    Column('normalized_value', REAL4),
    Column('influence_score', REAL4),
    schema='signals',
)

Index('ix_fusion_trace_proposal', signals_fusion_trace.c.proposal_id)
Index('ix_fusion_trace_module', signals_fusion_trace.c.module_id)

# 7) signals.snapshot — PARTITIONED
_SNAPSHOT_PARENT_DDL = """
CREATE TABLE IF NOT EXISTS signals.snapshot (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    asof timestamptz NOT NULL,
    session_date DATE,
    session_id TEXT,
    module_id BIGINT NOT NULL REFERENCES signals.module(id) ON DELETE CASCADE,
    asset_id BIGINT REFERENCES core.asset(id) ON DELETE SET NULL,
    value DOUBLE PRECISION NOT NULL,
    confidence REAL CHECK (confidence BETWEEN 0 AND 1),
    horizon INTERVAL,
    quality_flag TEXT,
    explain JSONB NOT NULL DEFAULT '{}'
) PARTITION BY RANGE (asof);
"""

_SNAPSHOT_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_snapshot_module_asof ON signals.snapshot (module_id, asof)",
    "CREATE INDEX IF NOT EXISTS ix_snapshot_asof_asset ON signals.snapshot (asof, asset_id)",
]

# =========================
# C) risk schema
# =========================

# 9) risk.limits
risk_limits = Table(
    'limits',
    metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('scope', sa.Text, nullable=False),
    Column('limit_kind', limit_kind, nullable=False),
    Column('hard_cap', sa.Numeric(20, 6)),
    Column('soft_cap', sa.Numeric(20, 6)),
    Column('valid_from', TIMESTAMPTZ),
    Column('valid_to', TIMESTAMPTZ),
    Column('notes', sa.Text),
    schema='risk',
)

# 10) risk.checks
risk_checks = Table(
    'checks',
    metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('proposal_id', sa.BigInteger, ForeignKey('core.policy_proposal.id', ondelete='CASCADE'), nullable=False),
    Column('asof', TIMESTAMPTZ, nullable=False),
    Column('check_name', sa.Text, nullable=False),
    Column('passed', sa.Boolean, nullable=False),
    Column('details', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    schema='risk',
)

Index('ix_risk_checks_proposal', risk_checks.c.proposal_id)

# 11) risk.verdict
risk_verdict = Table(
    'verdict',
    metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('proposal_id', sa.BigInteger, ForeignKey('core.policy_proposal.id', ondelete='CASCADE'), nullable=False),
    Column('asof', TIMESTAMPTZ, nullable=False),
    Column('status', verdict_status, nullable=False),
    Column('reason', sa.Text),
    Column('metrics', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    UniqueConstraint('proposal_id', name='uq_verdict_per_proposal'),
    schema='risk',
)

# =========================
# D) models schema
# =========================

# 12) models.feature_def
models_feature_def = Table(
    'feature_def',
    metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('name', sa.Text, nullable=False, unique=True),
    Column('spec', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column('owner', sa.Text),
    Column('is_active', sa.Boolean, nullable=False, server_default=text('true')),
    schema='models',
)

# 13) models.feature_store — PARTITIONED
_FEATURE_STORE_PARENT_DDL = """
CREATE TABLE IF NOT EXISTS models.feature_store (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    asof timestamptz NOT NULL,
    feature_id BIGINT NOT NULL REFERENCES models.feature_def(id) ON DELETE CASCADE,
    asset_id BIGINT REFERENCES core.asset(id) ON DELETE SET NULL,
    value DOUBLE PRECISION NOT NULL,
    lag INT
) PARTITION BY RANGE (asof);
"""

_FEATURE_STORE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_feature_store_feature_asof ON models.feature_store (feature_id, asof)",
    "CREATE INDEX IF NOT EXISTS ix_feature_store_asof_asset ON models.feature_store (asof, asset_id)",
]

# 14) models.hmm_spec
models_hmm_spec = Table(
    'hmm_spec',
    metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('name', sa.Text, nullable=False),
    Column('version', sa.Integer, nullable=False),
    Column('n_states', sa.Integer, nullable=False),
    Column('obs_family', sa.Text, nullable=False),
    Column('regime_labels', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column('init_params', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    UniqueConstraint('name', 'version', name='uq_hmm_spec_name_version'),
    schema='models',
)

# 17) models.training_run
models_training_run = Table(
    'training_run',
    metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('model_kind', sa.Text, nullable=False),
    Column('spec_id', sa.BigInteger),
    Column('data_window', DATERANGE),
    Column('seed', sa.Integer),
    Column('started_at', TIMESTAMPTZ),
    Column('finished_at', TIMESTAMPTZ),
    Column('status', sa.Text),
    Column('metrics', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column('artifact_uri', sa.Text),
    schema='models',
)

# 15) models.hmm_params
models_hmm_params = Table(
    'hmm_params',
    metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('hmm_spec_id', sa.BigInteger, ForeignKey('models.hmm_spec.id', ondelete='CASCADE'), nullable=False),
    Column('training_run_id', sa.BigInteger, ForeignKey('models.training_run.id', ondelete='SET NULL')),
    Column('pi', pg.ARRAY(DOUBLE), nullable=False),
    Column('a', pg.ARRAY(DOUBLE, dimensions=2), nullable=False),
    Column('emission', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column('fit_metrics', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    schema='models',
)

# 16) models.bayes_model
models_bayes_model = Table(
    'bayes_model',
    metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('name', sa.Text, nullable=False),
    Column('version', sa.Integer, nullable=False),
    Column('prior', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column('link_fn', sa.Text),
    Column('regularization', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    UniqueConstraint('name', 'version', name='uq_bayes_model_name_version'),
    schema='models',
)

# 18) models.inference_trace
models_inference_trace = Table(
    'inference_trace',
    metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('asof', TIMESTAMPTZ, nullable=False),
    Column('hmm_params_id', sa.BigInteger, ForeignKey('models.hmm_params.id', ondelete='SET NULL')),
    Column('state_post', pg.ARRAY(DOUBLE)),
    Column('viterbi_state', sa.Integer),
    Column('regime', regime_type),
    Column('confidence', REAL4),
    Column('bayes_model_id', sa.BigInteger, ForeignKey('models.bayes_model.id', ondelete='SET NULL')),
    Column('posterior_weights', JSONB),
    Column('uncertainty', REAL4),
    CheckConstraint('confidence IS NULL OR (confidence >= 0 AND confidence <= 1)', name='ck_infer_conf_0_1'),
    schema='models',
)

Index('ix_inference_trace_asof', models_inference_trace.c.asof)

# =========================
# E) audit schema
# =========================

# 19) audit.event — PARTITIONED
_AUDIT_EVENT_PARENT_DDL = """
CREATE TABLE IF NOT EXISTS audit.event (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    asof timestamptz NOT NULL,
    emitter TEXT NOT NULL,
    event_type TEXT NOT NULL,
    entity_type TEXT,
    entity_id UUID,
    payload JSONB NOT NULL DEFAULT '{}',
    trace_id TEXT
) PARTITION BY RANGE (asof);
"""

_AUDIT_EVENT_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_audit_event_asof ON audit.event (asof)",
    "CREATE INDEX IF NOT EXISTS ix_audit_event_trace ON audit.event (trace_id)",
]

# 20) audit.change_log
audit_change_log = Table(
    'change_log',
    metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('who', sa.Text),
    Column('asof', TIMESTAMPTZ, nullable=False),
    Column('object_type', sa.Text, nullable=False),
    Column('object_id', sa.BigInteger),
    Column('before', JSONB),
    Column('after', JSONB),
    Column('message', sa.Text),
    schema='audit',
)

# =========================
# F) ops schema
# =========================

# 21) ops.review_queue
ops_review_queue = Table(
    'review_queue',
    metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('proposal_id', sa.BigInteger, ForeignKey('core.policy_proposal.id', ondelete='CASCADE'), nullable=False),
    Column('inserted_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('tier', sa.Integer, nullable=False),
    Column('reason', sa.Text),
    schema='ops',
)

Index('ix_review_queue_proposal', ops_review_queue.c.proposal_id)

# 22) ops.review_action
ops_review_action = Table(
    'review_action',
    metadata,
    Column('id', sa.BigInteger, sa.Identity(always=False), primary_key=True),
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('review_queue_id', sa.BigInteger, ForeignKey('ops.review_queue.id', ondelete='CASCADE'), nullable=False),
    Column('acted_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('actor', sa.Text, nullable=False),
    Column('action', human_action, nullable=False),
    Column('delta', JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column('comment', sa.Text),
    schema='ops',
)

# 23) ops.run_status
ops_run_status = Table(
    'run_status',
    metadata,
    Column('created_at', TIMESTAMPTZ, nullable=False, server_default=text('now()')),
    Column('asof', TIMESTAMPTZ, nullable=False),
    Column('component', sa.Text, nullable=False),
    Column('status', sa.Text, nullable=False),
    Column('latency_ms', sa.Integer),
    Column('error', sa.Text),
    PrimaryKeyConstraint('asof', 'component', name='pk_ops_run_status'),
    schema='ops',
)

# =========================
# Partition helper (shared)
# =========================

def _yyyymm_to_date(yyyymm: str) -> _dt.date:
    y = int(yyyymm[:4])
    m = int(yyyymm[4:6])
    return _dt.date(y, m, 1)


def _next_month(d: _dt.date) -> _dt.date:
    return _dt.date(
        d.year + (1 if d.month == 12 else 0),
        1 if d.month == 12 else d.month + 1,
        1,
    )


def _ensure_monthly_partitions(conn, parent: str, from_yyyymm: str, to_yyyymm: str) -> None:
    """Create monthly RANGE partitions [from_yyyymm, to_yyyymm] for a table partitioned by (asof)."""
    start = _yyyymm_to_date(from_yyyymm)
    end_last = _yyyymm_to_date(to_yyyymm)
    cur = start
    while cur <= end_last:
        nxt = _next_month(cur)
        suffix = f"{cur.year:04d}_{cur.month:02d}"
        ddl = f"""
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = split_part('{parent}', '.', 1)
          AND c.relname = split_part('{parent}', '.', 2) || '_{suffix}'
    ) THEN
        EXECUTE format(
            'CREATE TABLE %I.%I PARTITION OF {parent} FOR VALUES FROM (%L) TO (%L);',
            split_part('{parent}', '.', 1),
            split_part('{parent}', '.', 2) || '_{suffix}',
            '{cur.isoformat()}',
            '{nxt.isoformat()}'
        );
    END IF;
END$$;
"""
        conn.exec_driver_sql(ddl)
        cur = nxt

# =========================
# Bootstrap (one-shot)
# =========================

def bootstrap_hitherto(
    database_url: str,
    partitions: dict[str, tuple[str, str]] | None = None,
) -> None:
    """Create all schemas, enums, tables, partition parents and indexes."""
    engine = sa.create_engine(database_url, future=True)
    with engine.begin() as conn:
        # Schemas
        for s in ('core', 'signals', 'risk', 'models', 'audit', 'ops'):
            conn.exec_driver_sql(f"CREATE SCHEMA IF NOT EXISTS {s}")

        # Enums
        for enum in (
            regime_type,
            verdict_status,
            proposal_status,
            human_action,
            limit_kind,
        ):
            enum.create(conn, checkfirst=True)

        # SA-managed tables
        metadata.create_all(conn, checkfirst=True)

        # Partition parents
        conn.exec_driver_sql(_SNAPSHOT_PARENT_DDL)
        conn.exec_driver_sql(_FEATURE_STORE_PARENT_DDL)
        conn.exec_driver_sql(_AUDIT_EVENT_PARENT_DDL)

        for stmt in _SNAPSHOT_INDEXES:
            conn.exec_driver_sql(stmt)
        for stmt in _FEATURE_STORE_INDEXES:
            conn.exec_driver_sql(stmt)
        for stmt in _AUDIT_EVENT_INDEXES:
            conn.exec_driver_sql(stmt)

        if partitions:
            if 'signals_snapshot' in partitions:
                a, b = partitions['signals_snapshot']
                _ensure_monthly_partitions(conn, 'signals.snapshot', a, b)
            if 'models_feature_store' in partitions:
                a, b = partitions['models_feature_store']
                _ensure_monthly_partitions(conn, 'models.feature_store', a, b)
            if 'audit_event' in partitions:
                a, b = partitions['audit_event']
                _ensure_monthly_partitions(conn, 'audit.event', a, b)


if __name__ == "__main__":
    # Example usage (disabled):
    # DATABASE_URL = "postgresql+psycopg://user:pass@localhost:5432/hitherto"
    # bootstrap_hitherto(
    #     DATABASE_URL,
    #     partitions={
    #         "signals_snapshot": ("202401", "202612"),
    #         "models_feature_store": ("202401", "202612"),
    #         "audit_event": ("202401", "202612"),
    #     },
    # )
    pass
