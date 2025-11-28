"""add geo and payment providers

Revision ID: c2f9a1e7d3b4
Revises: b884acf6ba3a
Create Date: 2025-11-26 21:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, Integer


# revision identifiers, used by Alembic.
revision = 'c2f9a1e7d3b4'
down_revision = 'b884acf6ba3a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'countries',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('code', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(), nullable=False),
    )

    op.create_table(
        'payment_providers',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('code', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
    )

    op.create_table(
        'country_payment_providers',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('country_id', sa.Integer(), sa.ForeignKey('countries.id'), nullable=False),
        sa.Column('provider_id', sa.Integer(), sa.ForeignKey('payment_providers.id'), nullable=False),
        sa.Column('is_supported', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.UniqueConstraint('country_id', 'provider_id', name='uq_country_provider'),
    )


def downgrade() -> None:
    op.drop_table('country_payment_providers')
    op.drop_table('payment_providers')
    op.drop_table('countries')
