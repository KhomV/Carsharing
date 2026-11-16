"""create car_telemetry table

Revision ID: 001_telemetry
Revises: 
Create Date: 2026-11-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_telemetry'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'car_telemetry',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('car_id', sa.UUID(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('fuel_level', sa.Integer(), nullable=False),
        sa.Column('mileage', sa.Integer(), nullable=False),
        sa.Column('is_engine_on', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_handbrake_engaged', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('latitude >= -90.0 AND latitude <= 90.0', name='ck_telemetry_latitude'),
        sa.CheckConstraint('longitude >= -180.0 AND longitude <= 180.0', name='ck_telemetry_longitude'),
        sa.CheckConstraint('fuel_level >= 0 AND fuel_level <= 100', name='ck_telemetry_fuel_level'),
        sa.CheckConstraint('mileage >= 0', name='ck_telemetry_mileage'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_car_telemetry_car_id', 'car_telemetry', ['car_id'], unique=False)
    op.create_index('ix_car_telemetry_car_created', 'car_telemetry', ['car_id', sa.text('created_at DESC')], unique=False)


def downgrade() -> None:
    op.drop_index('ix_car_telemetry_car_created', table_name='car_telemetry')
    op.drop_index('ix_car_telemetry_car_id', table_name='car_telemetry')
    op.drop_table('car_telemetry')
