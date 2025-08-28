"""PostgreSQL schema design for LLM message logging (brand new).

This file defines the RELATIONAL schema (PostgreSQL‑centric) for capturing all
LLM messages & related telemetry inside the Hitherto framework. It intentionally
does NOT reuse prior in‑memory / Pydantic drafts; we're starting fresh focusing
on a durable, query‑friendly shape.

Goals
-----
1. Efficient conversation reconstruction (ordered by conversation + seq).
2. Provider/model attribution & cost accounting.
3. Robust error / status visibility.
4. Flexible metadata (JSONB) without sacrificing indexable core columns.
5. Extensible for future: embeddings, tool events, guardrail audits.

Core Entities (initial cut)
--------------------------
* llm_message_log: single row per message (user/system/assistant/tool).
  Potential future split (messages vs. traces) postponed until needed.

Enumerations
------------
* message_role_enum: system | user | assistant | tool
* message_status_enum: sent | error | cached
* priority_enum: low | normal | high | critical

Key Design Choices
------------------
* UUID primary keys for global uniqueness across distributed workers.
* conversation_id (UUID) groups messages; sequence_number (INT) provides
  deterministic ordering and allows intra‑conversation paging.
* created_at timestamptz defaults to NOW() for chronological queries/TTL.
* TEXT for provider/model to avoid early rigid FKs; can normalize later.
* JSONB metadata for sparse provider‑specific attributes (usage, safety flags).
* Optional numeric(18,6) cost for precise currency accumulation.
* GIN index on metadata for ad‑hoc filtering (optional, can add later).
* Partial index for fast retrieval of recent assistant outputs if needed.

SQL DDL (reference)
-------------------
The below DDL is provided as a canonical starting point. Apply via Alembic or
manual migration process. (Naming: singular enums, snake_case columns.)
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import (
	Column,
	String,
	Text,
	Integer,
	Float,
	Numeric,
	Boolean,
	DateTime,
	ForeignKey,
	JSON,
	MetaData,
	Index,
	Enum,
	text,
	func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, Mapped, mapped_column


# Central metadata (can integrate with existing metadata if project already has one)
metadata = MetaData()
Base = declarative_base(metadata=metadata)


MESSAGE_ROLE_ENUM = ("system", "user", "assistant", "tool")
MESSAGE_STATUS_ENUM = ("sent", "error", "cached")
PRIORITY_ENUM = ("low", "normal", "high", "critical")


class LLMMessageLog(Base):  # type: ignore
	"""Relational table mapping for all LLM messages.

	Column Summary
	--------------
	id (UUID PK)                 : Unique row id.
	conversation_id (UUID)       : Groups messages into a logical session.
	parent_message_id (UUID FK?) : Optional link to prior message (threading / reply tree).
	sequence_number (INT)        : Monotonic per conversation for deterministic ordering.
	role (ENUM)                  : Actor role (system/user/assistant/tool).
	status (ENUM)                : Delivery outcome (sent/error/cached).
	priority (ENUM)              : Importance (low/normal/high/critical).
	provider_name (TEXT)         : Internal provider key (e.g. "openai").
	model_name (TEXT)            : External model id.
	context_module (TEXT)        : Originating module providing structured context.
	content (TEXT)               : Raw message text (prompt or completion).
	truncated (BOOLEAN)          : Indicates content was truncated for storage.
	tokens_input (INT)           : Input tokens (prompt side) if known.
	tokens_output (INT)          : Output tokens (completion) if known.
	latency_ms (FLOAT)           : Provider round‑trip latency.
	cost (NUMERIC(18,6))         : Monetary cost attribution (USD or canonical).
	error_type (TEXT)            : Categorical error label.
	error_message (TEXT)         : Human readable error detail.
	metadata (JSONB)             : Provider / framework extras (usage breakdown etc.).
	created_at (TIMESTAMPTZ)     : Insertion timestamp (default now()).
	updated_at (TIMESTAMPTZ)     : Updated timestamp (ON UPDATE trigger or app managed).
	version (INT)                : Optimistic concurrency / future edits.
	reserved1..n                 : Placeholder columns for forward schema evolution (omitted now).
	"""

	__tablename__ = "llm_message_log"

	id: Mapped[str] = mapped_column(
		UUID(as_uuid=False), primary_key=True, default=lambda: uuid4().hex
	)
	conversation_id: Mapped[Optional[str]] = mapped_column(
		UUID(as_uuid=False), index=True, nullable=True
	)
	parent_message_id: Mapped[Optional[str]] = mapped_column(
		UUID(as_uuid=False), ForeignKey("llm_message_log.id", ondelete="SET NULL"), nullable=True
	)
	sequence_number: Mapped[Optional[int]] = mapped_column(
		Integer, nullable=True, comment="Monotonic per conversation; assign externally"
	)

	role: Mapped[str] = mapped_column(
		Enum(*MESSAGE_ROLE_ENUM, name="message_role_enum", create_type=False), nullable=False
	)
	status: Mapped[str] = mapped_column(
		Enum(*MESSAGE_STATUS_ENUM, name="message_status_enum", create_type=False),
		nullable=False,
		default="sent",
		server_default=text("'sent'"),
	)
	priority: Mapped[Optional[str]] = mapped_column(
		Enum(*PRIORITY_ENUM, name="priority_enum", create_type=False), nullable=True
	)

	provider_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
	model_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True, index=True)
	context_module: Mapped[Optional[str]] = mapped_column(String(150), nullable=True, index=True)

	content: Mapped[str] = mapped_column(Text, nullable=False)
	truncated: Mapped[bool] = mapped_column(
		Boolean, nullable=False, default=False, server_default=text("false")
	)

	tokens_input: Mapped[Optional[int]] = mapped_column(Integer)
	tokens_output: Mapped[Optional[int]] = mapped_column(Integer)
	latency_ms: Mapped[Optional[float]] = mapped_column(Float)
	cost: Mapped[Optional[float]] = mapped_column(Numeric(18, 6))

	error_type: Mapped[Optional[str]] = mapped_column(String(120))
	error_message: Mapped[Optional[str]] = mapped_column(Text)

	metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)

	created_at: Mapped[str] = mapped_column(
		DateTime(timezone=True), nullable=False, server_default=func.now()
	)
	updated_at: Mapped[Optional[str]] = mapped_column(
		DateTime(timezone=True), nullable=True, onupdate=func.now()
	)

	version: Mapped[int] = mapped_column(
		Integer,
		nullable=False,
		default=1,
		server_default=text("1"),
		comment="Row version for optimistic locking",
	)

	# Derived / convenience (not stored) could be added via hybrid properties later.

	__table_args__ = (
		# Order guarantee within conversation (optionally UNIQUE if sequence enforced)
		Index(
			"ix_llm_message_log_conversation_seq",
			"conversation_id",
			"sequence_number",
		),
		# Fast time-ordered scans for a given conversation
		Index(
			"ix_llm_message_log_conversation_created",
			"conversation_id",
			"created_at",
		),
		# Frequent filter combos
		Index(
			"ix_llm_message_log_provider_model",
			"provider_name",
			"model_name",
		),
		# Optional: partial index could be added via migration for assistant only rows
		# (example shown in MIGRATION_NOTES string below)
	)

	def to_dict(self) -> Dict[str, Any]:  # lightweight serializer
		return {c.name: getattr(self, c.name) for c in self.__table__.columns}


SCHEMA_DDL: str = """
-- ENUM Types (idempotent creation pattern)
DO $$ BEGIN
	IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'message_role_enum') THEN
		CREATE TYPE message_role_enum AS ENUM ('system','user','assistant','tool');
	END IF;
END $$;

DO $$ BEGIN
	IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'message_status_enum') THEN
		CREATE TYPE message_status_enum AS ENUM ('sent','error','cached');
	END IF;
END $$;

DO $$ BEGIN
	IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'priority_enum') THEN
		CREATE TYPE priority_enum AS ENUM ('low','normal','high','critical');
	END IF;
END $$;

CREATE TABLE IF NOT EXISTS llm_message_log (
	id                uuid PRIMARY KEY,
	conversation_id   uuid NULL,
	parent_message_id uuid NULL REFERENCES llm_message_log(id) ON DELETE SET NULL,
	sequence_number   integer NULL,
	role              message_role_enum NOT NULL,
	status            message_status_enum NOT NULL DEFAULT 'sent',
	priority          priority_enum NULL,
	provider_name     varchar(100) NULL,
	model_name        varchar(150) NULL,
	context_module    varchar(150) NULL,
	content           text NOT NULL,
	truncated         boolean NOT NULL DEFAULT false,
	tokens_input      integer NULL,
	tokens_output     integer NULL,
	latency_ms        double precision NULL,
	cost              numeric(18,6) NULL,
	error_type        varchar(120) NULL,
	error_message     text NULL,
	metadata          jsonb NULL,
	created_at        timestamptz NOT NULL DEFAULT now(),
	updated_at        timestamptz NULL,
	version           integer NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS ix_llm_message_log_conversation_seq
	ON llm_message_log (conversation_id, sequence_number);
CREATE INDEX IF NOT EXISTS ix_llm_message_log_conversation_created
	ON llm_message_log (conversation_id, created_at);
CREATE INDEX IF NOT EXISTS ix_llm_message_log_provider_model
	ON llm_message_log (provider_name, model_name);
CREATE INDEX IF NOT EXISTS ix_llm_message_log_context_module
	ON llm_message_log (context_module);
-- (Optional) GIN index on metadata for key existence / containment queries
-- CREATE INDEX IF NOT EXISTS ix_llm_message_log_metadata ON llm_message_log USING GIN (metadata);
-- (Optional) Partial index for recent assistant messages
-- CREATE INDEX IF NOT EXISTS ix_llm_message_log_recent_assistant ON llm_message_log (created_at)
--   WHERE role = 'assistant' AND created_at > now() - interval '7 days';
""".strip()


MIGRATION_NOTES = """
Future Additions / Alterations
------------------------------
1. Embeddings:  ALTER TABLE llm_message_log ADD COLUMN embedding vector(1536);
   (Requires pgvector extension: CREATE EXTENSION IF NOT EXISTS vector;)
2. Guardrail Flags: ADD COLUMN safety_labels jsonb;
3. Conversation-Level Aggregates: Create separate table 'conversation_summary'.
4. Sequence Enforcement: Add UNIQUE (conversation_id, sequence_number) once all writers set it.
5. Partitioning: RANGE (created_at) or HASH (conversation_id) if volume mandates.
""".strip()


def create_schema(engine) -> None:
	"""Programmatic creation: ensures ENUM types then creates tables.

	Use for initial bootstrap or in migration scripts. For production, prefer
	Alembic migrations referencing the DDL constants for auditability.
	"""
	with engine.begin() as conn:
		# Create ENUM types (idempotent)
		for enum_name, values in [
			("message_role_enum", MESSAGE_ROLE_ENUM),
			("message_status_enum", MESSAGE_STATUS_ENUM),
			("priority_enum", PRIORITY_ENUM),
		]:
			existing = conn.execute(
				text("SELECT 1 FROM pg_type WHERE typname = :n"), {"n": enum_name}
			).scalar()
			if not existing:
				conn.execute(
					text(
						f"CREATE TYPE {enum_name} AS ENUM (" + ",".join(f"'{v}'" for v in values) + ")"
					)
				)
		# Create tables
		Base.metadata.create_all(bind=conn)


__all__ = [
	"LLMMessageLog",
	"create_schema",
	"SCHEMA_DDL",
	"MIGRATION_NOTES",
	"metadata",
	"Base",
]

