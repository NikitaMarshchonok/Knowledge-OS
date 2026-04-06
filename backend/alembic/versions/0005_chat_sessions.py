"""reserved revision after chat scope rollback

Revision ID: 0005_chat_sessions
Revises: 0004_ask_run_evaluation_layer
Create Date: 2026-03-30

"""

# revision identifiers, used by Alembic.
revision = "0005_chat_sessions"
down_revision = "0004_ask_run_evaluation_layer"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Intentionally no-op. This revision id is kept to preserve migration continuity.
    pass


def downgrade() -> None:
    pass
