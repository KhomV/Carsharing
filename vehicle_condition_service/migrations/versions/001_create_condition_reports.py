from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "condition_reports",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("car_id", sa.Uuid(), nullable=False),
        sa.Column("reference_id", sa.Uuid(), nullable=False),
        sa.Column("phase", sa.String(6), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("photos", JSONB(), nullable=False),
        sa.UniqueConstraint("phase", "reference_id", name="uq_condition_reports_reference"),
        sa.CheckConstraint("phase IN ('before', 'after')", name="ck_condition_reports_phase"),
    )


def downgrade() -> None:
    op.drop_table("condition_reports")
