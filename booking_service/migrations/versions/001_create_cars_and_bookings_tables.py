"""create cars and bookings tables

Revision ID: 001_booking
Revises: 
Create Date: 2026-11-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_booking'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'cars',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('plate_number', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('price_per_minute', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('available', 'booked', 'rented', 'maintenance')",
            name='ck_cars_status',
        ),
        sa.CheckConstraint('price_per_minute > 0', name='ck_cars_price_positive'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plate_number', name='uq_cars_plate_number'),
    )

    op.create_table(
        'bookings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('car_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('active', 'cancelled', 'completed')",
            name='ck_bookings_status',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_bookings_user_id', 'bookings', ['user_id'], unique=False)
    op.create_index('ix_bookings_car_id', 'bookings', ['car_id'], unique=False)
    op.create_index(
        'uq_active_booking_car',
        'bookings',
        ['car_id'],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    op.drop_index(
        'uq_active_booking_car',
        table_name='bookings',
        postgresql_where=sa.text("status = 'active'"),
    )
    op.drop_index('ix_bookings_car_id', table_name='bookings')
    op.drop_index('ix_bookings_user_id', table_name='bookings')
    op.drop_table('bookings')
    op.drop_table('cars')
