"""ask run evaluation layer

Revision ID: 0004_ask_run_evaluation_layer
Revises: 0003_document_indexing_metadata
Create Date: 2026-03-30

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0004_ask_run_evaluation_layer"
down_revision = "0003_document_indexing_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    ask_run_status = postgresql.ENUM("success", "failed", "insufficient_evidence", name="ask_run_status")
    ask_run_status.create(op.get_bind(), checkfirst=True)

    feedback_rating = postgresql.ENUM("positive", "negative", name="feedback_rating")
    feedback_rating.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "ask_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("success", "failed", "insufficient_evidence", name="ask_run_status"),
            nullable=False,
        ),
        sa.Column("llm_model", sa.String(length=255), nullable=True),
        sa.Column("embedding_model", sa.String(length=255), nullable=True),
        sa.Column("rerank_model", sa.String(length=255), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("top_k", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retrieved_chunk_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("reranked_chunk_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("cited_chunk_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ask_runs_project_created", "ask_runs", ["project_id", "created_at"], unique=False)
    op.create_index("ix_ask_runs_status_created", "ask_runs", ["status", "created_at"], unique=False)

    op.create_table(
        "ask_run_citations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ask_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("char_start", sa.Integer(), nullable=False),
        sa.Column("char_end", sa.Integer(), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=False),
        sa.Column("citation_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["ask_run_id"], ["ask_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ask_run_citations_run_order", "ask_run_citations", ["ask_run_id", "citation_order"], unique=False)

    op.create_table(
        "ask_run_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ask_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rating", sa.Enum("positive", "negative", name="feedback_rating"), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["ask_run_id"], ["ask_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ask_run_id", name="uq_ask_run_feedback_ask_run_id"),
    )


def downgrade() -> None:
    op.drop_table("ask_run_feedback")
    op.drop_index("ix_ask_run_citations_run_order", table_name="ask_run_citations")
    op.drop_table("ask_run_citations")
    op.drop_index("ix_ask_runs_status_created", table_name="ask_runs")
    op.drop_index("ix_ask_runs_project_created", table_name="ask_runs")
    op.drop_table("ask_runs")

    feedback_rating = postgresql.ENUM("positive", "negative", name="feedback_rating")
    feedback_rating.drop(op.get_bind(), checkfirst=True)

    ask_run_status = postgresql.ENUM("success", "failed", "insufficient_evidence", name="ask_run_status")
    ask_run_status.drop(op.get_bind(), checkfirst=True)
