"""document indexing metadata

Revision ID: 0003_document_indexing_metadata
Revises: 0002_document_processing_pipeline
Create Date: 2026-03-29

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0003_document_indexing_metadata"
down_revision = "0002_document_processing_pipeline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("is_indexing", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("documents", sa.Column("indexing_error", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "indexed_at")
    op.drop_column("documents", "indexing_error")
    op.drop_column("documents", "is_indexing")
