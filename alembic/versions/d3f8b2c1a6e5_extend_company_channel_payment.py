"""extend company, channel and payment

Revision ID: d3f8b2c1a6e5
Revises: c2f9a1e7d3b4
Create Date: 2025-11-26 21:41:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd3f8b2c1a6e5'
down_revision = 'c2f9a1e7d3b4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # companies: add country_code, telegram_bot_token, telegram_default_group_id
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    company_cols = [c['name'] for c in inspector.get_columns('companies')]
    if 'country_code' not in company_cols:
        op.add_column('companies', sa.Column('country_code', sa.String(), nullable=True))
    if 'telegram_bot_token' not in company_cols:
        op.add_column('companies', sa.Column('telegram_bot_token', sa.String(), nullable=True))
    if 'telegram_default_group_id' not in company_cols:
        op.add_column('companies', sa.Column('telegram_default_group_id', sa.String(), nullable=True))

    # channels: add provider_id FK to payment_providers
    # Use batch_alter_table to support SQLite ALTER emulation
    from alembic import op as _op
    with _op.batch_alter_table('channels', recreate='always') as batch_op:
        batch_op.add_column(sa.Column('provider_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_channels_provider_id_payment_providers', 'payment_providers', ['provider_id'], ['id'])

    # payments: add confirm_token and index
    payment_cols = [c['name'] for c in inspector.get_columns('payments')]
    if 'confirm_token' not in payment_cols:
        op.add_column('payments', sa.Column('confirm_token', sa.String(), nullable=True))
    # create index if not exists
    indexes = [ix['name'] for ix in inspector.get_indexes('payments')]
    if 'ix_payments_confirm_token' not in indexes:
        op.create_index(op.f('ix_payments_confirm_token'), 'payments', ['confirm_token'], unique=False)


def downgrade() -> None:
    # payments: drop index then column (if exist)
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = [ix['name'] for ix in inspector.get_indexes('payments')]
    if 'ix_payments_confirm_token' in indexes:
        op.drop_index(op.f('ix_payments_confirm_token'), table_name='payments')
    cols = [c['name'] for c in inspector.get_columns('payments')]
    if 'confirm_token' in cols:
        op.drop_column('payments', 'confirm_token')

    # channels: drop FK then column (use batch_alter_table for SQLite)
    from alembic import op as _op
    with _op.batch_alter_table('channels', recreate='always') as batch_op:
        batch_op.drop_constraint('fk_channels_provider_id_payment_providers', type_='foreignkey')
        batch_op.drop_column('provider_id')

    # companies: drop telegram and country columns
    op.drop_column('companies', 'telegram_default_group_id')
    op.drop_column('companies', 'telegram_bot_token')
    op.drop_column('companies', 'country_code')
