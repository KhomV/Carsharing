from alembic import op
import sqlalchemy as sa


revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "driver_licenses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("account_id", sa.Uuid(), nullable=False, unique=True),
        sa.Column("expires_on", sa.Date(), nullable=False),
        sa.Column("number_last_four", sa.String(4), nullable=False),
        sa.Column("status", sa.String(8), nullable=False),
        sa.Column("reason", sa.String(40), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'verified', 'rejected')",
            name="ck_driver_licenses_status",
        ),
    )


def downgrade() -> None:
    op.drop_table("driver_licenses")
