"""document processing pipeline foundation

Revision ID: 0002_document_processing_pipeline
Revises: 0001_initial
Create Date: 2026-03-29

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002_doc_processing"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE document_status ADD VALUE IF NOT EXISTS 'processed'")

    op.add_column("documents", sa.Column("processing_error", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("documents", sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("documents", sa.Column("extracted_text_path", sa.String(length=500), nullable=True))
    op.add_column("documents", sa.Column("page_count", sa.Integer(), nullable=True))

    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("char_start", sa.Integer(), nullable=False),
        sa.Column("char_end", sa.Integer(), nullable=False),
        sa.Column("token_estimate", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_document_id_chunk_index"),
    )


def downgrade() -> None:
    op.drop_table("document_chunks")

    op.drop_column("documents", "page_count")
    op.drop_column("documents", "extracted_text_path")
    op.drop_column("documents", "chunk_count")
    op.drop_column("documents", "processed_at")
    op.drop_column("documents", "processing_error")

    op.execute("UPDATE documents SET status = 'failed' WHERE status = 'processed'")
    op.execute("ALTER TYPE document_status RENAME TO document_status_old")
    op.execute("CREATE TYPE document_status AS ENUM ('uploaded', 'processing', 'indexed', 'failed')")
    op.execute(
        "ALTER TABLE documents ALTER COLUMN status TYPE document_status USING status::text::document_status"
    )
    op.execute("DROP TYPE document_status_old")
