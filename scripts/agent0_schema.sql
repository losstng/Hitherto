-- Schema initialization for Agent 0 core tables and supporting namespaces
-- Generated according to project conventions (timestamptz, jsonb, surrogate keys)

-- Enumerated types
CREATE TYPE regime_type AS ENUM ('BULL','BEAR','NEUTRAL','UNKNOWN');
CREATE TYPE proposal_status AS ENUM ('DRAFT','UNDER_REVIEW','APPROVED','REJECTED');
CREATE TYPE verdict_status AS ENUM ('APPROVED','DOWNGRADED','REJECTED','TIGHTEN');
CREATE TYPE human_action AS ENUM ('APPROVE','REJECT','MODIFY','ASK_RISK');
CREATE TYPE limit_kind AS ENUM ('POSITION','EXPOSURE','VAR','OTHER');

-- Namespaces
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS signals;
CREATE SCHEMA IF NOT EXISTS risk;
CREATE SCHEMA IF NOT EXISTS models;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS ops;

-- Core tables
CREATE TABLE core.regime_state (
    id BIGSERIAL PRIMARY KEY,
    asof TIMESTAMPTZ NOT NULL,
    regime regime_type NOT NULL,
    confidence REAL NOT NULL,
    hysteresis_lock_until TIMESTAMPTZ,
    source TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE core.playbook (
    id BIGSERIAL PRIMARY KEY,
    version INT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    valid_from TIMESTAMPTZ,
    valid_to TIMESTAMPTZ,
    name TEXT NOT NULL,
    notes TEXT,
    weights JSONB,
    thresholds JSONB,
    tiers JSONB,
    horizons JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS playbook_one_active ON core.playbook (is_active) WHERE is_active;

CREATE TABLE core.policy_proposal (
    id BIGSERIAL PRIMARY KEY,
    asof TIMESTAMPTZ NOT NULL,
    regime_state_id BIGINT REFERENCES core.regime_state(id),
    playbook_id BIGINT REFERENCES core.playbook(id),
    status proposal_status NOT NULL,
    targets JSONB,
    rationale JSONB,
    metrics JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE core.decision (
    id BIGSERIAL PRIMARY KEY,
    proposal_id BIGINT REFERENCES core.policy_proposal(id),
    asof TIMESTAMPTZ NOT NULL,
    decider TEXT NOT NULL,
    notes TEXT,
    orders JSONB,
    constraints_checked JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE core.asset (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    venue TEXT,
    currency TEXT,
    lot_size NUMERIC,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE core.portfolio_snapshot (
    id BIGSERIAL PRIMARY KEY,
    asof TIMESTAMPTZ NOT NULL,
    positions JSONB,
    cash NUMERIC,
    gross_exposure NUMERIC,
    net_exposure NUMERIC,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Signals tables
CREATE TABLE signals.module (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    family TEXT,
    owner TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    expected_horizon INTERVAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE signals.snapshot (
    id BIGSERIAL PRIMARY KEY,
    asof TIMESTAMPTZ NOT NULL,
    module_id BIGINT REFERENCES signals.module(id),
    asset_id BIGINT REFERENCES core.asset(id),
    value DOUBLE PRECISION,
    confidence REAL,
    horizon INTERVAL,
    quality_flag TEXT,
    explain JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS snapshot_module_asof_idx ON signals.snapshot (module_id, asof);

CREATE TABLE signals.fusion_trace (
    id BIGSERIAL PRIMARY KEY,
    proposal_id BIGINT REFERENCES core.policy_proposal(id),
    module_id BIGINT REFERENCES signals.module(id),
    weight REAL,
    normalized_value REAL,
    influence_score REAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Risk tables
CREATE TABLE risk.limits (
    id BIGSERIAL PRIMARY KEY,
    scope TEXT NOT NULL,
    limit_kind limit_kind NOT NULL,
    hard_cap NUMERIC,
    soft_cap NUMERIC,
    valid_from TIMESTAMPTZ,
    valid_to TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE risk.checks (
    id BIGSERIAL PRIMARY KEY,
    proposal_id BIGINT REFERENCES core.policy_proposal(id),
    asof TIMESTAMPTZ NOT NULL,
    check_name TEXT NOT NULL,
    passed BOOLEAN NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE risk.verdict (
    id BIGSERIAL PRIMARY KEY,
    proposal_id BIGINT REFERENCES core.policy_proposal(id) UNIQUE,
    asof TIMESTAMPTZ NOT NULL,
    status verdict_status NOT NULL,
    reason TEXT,
    metrics JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Models tables
CREATE TABLE models.feature_def (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    spec JSONB,
    owner TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE models.feature_store (
    id BIGSERIAL PRIMARY KEY,
    asof TIMESTAMPTZ NOT NULL,
    feature_id BIGINT REFERENCES models.feature_def(id),
    asset_id BIGINT REFERENCES core.asset(id),
    value DOUBLE PRECISION,
    lag INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS feature_store_feature_asof_idx ON models.feature_store (feature_id, asof);

CREATE TABLE models.hmm_spec (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    version INT NOT NULL,
    n_states INT,
    obs_family TEXT,
    regime_labels JSONB,
    init_params JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE models.hmm_params (
    id BIGSERIAL PRIMARY KEY,
    hmm_spec_id BIGINT REFERENCES models.hmm_spec(id),
    training_run_id BIGINT,
    pi DOUBLE PRECISION[],
    A DOUBLE PRECISION[][],
    emission JSONB,
    fit_metrics JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE models.bayes_model (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    version INT NOT NULL,
    prior JSONB,
    link_fn TEXT,
    regularization JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE models.training_run (
    id BIGSERIAL PRIMARY KEY,
    model_kind TEXT NOT NULL,
    spec_id BIGINT,
    data_window DATERANGE,
    seed INT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    status TEXT,
    metrics JSONB,
    artifact_uri TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE models.inference_trace (
    id BIGSERIAL PRIMARY KEY,
    asof TIMESTAMPTZ NOT NULL,
    hmm_params_id BIGINT REFERENCES models.hmm_params(id),
    state_post DOUBLE PRECISION[],
    viterbi_state INT,
    regime regime_type,
    confidence REAL,
    bayes_model_id BIGINT REFERENCES models.bayes_model(id),
    posterior_weights JSONB,
    uncertainty REAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit tables
CREATE TABLE audit.event (
    id BIGSERIAL PRIMARY KEY,
    emitter TEXT NOT NULL,
    asof TIMESTAMPTZ NOT NULL,
    event_type TEXT NOT NULL,
    entity_type TEXT,
    entity_id UUID,
    payload JSONB,
    trace_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE audit.change_log (
    id BIGSERIAL PRIMARY KEY,
    who TEXT,
    asof TIMESTAMPTZ NOT NULL,
    object_type TEXT,
    object_id BIGINT,
    before JSONB,
    after JSONB,
    message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ops tables
CREATE TABLE ops.review_queue (
    id BIGSERIAL PRIMARY KEY,
    proposal_id BIGINT REFERENCES core.policy_proposal(id),
    inserted_at TIMESTAMPTZ NOT NULL,
    tier INT,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ops.review_action (
    id BIGSERIAL PRIMARY KEY,
    review_queue_id BIGINT REFERENCES ops.review_queue(id),
    acted_at TIMESTAMPTZ NOT NULL,
    actor TEXT,
    action human_action NOT NULL,
    delta JSONB,
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ops.run_status (
    id BIGSERIAL PRIMARY KEY,
    asof TIMESTAMPTZ NOT NULL,
    component TEXT NOT NULL,
    status TEXT NOT NULL,
    latency_ms INT,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for hot paths
CREATE INDEX IF NOT EXISTS regime_state_recent_idx ON core.regime_state (asof DESC) WHERE asof > now() - INTERVAL '180 days';
CREATE INDEX IF NOT EXISTS policy_proposal_asof_idx ON core.policy_proposal (asof);
CREATE INDEX IF NOT EXISTS risk_verdict_proposal_idx ON risk.verdict (proposal_id);

