from alembic import op
import sqlalchemy as sa


revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("password_hash", sa.String(128), nullable=False),
    )
    op.create_table(
        "auth_sessions",
        sa.Column("token_digest", sa.String(64), primary_key=True),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_auth_sessions_account_id", "auth_sessions", ["account_id"])


def downgrade() -> None:
    op.drop_table("auth_sessions")
    op.drop_table("accounts")
