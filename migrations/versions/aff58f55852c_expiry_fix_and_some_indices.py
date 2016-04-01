"""Expiry fix and some indices

Revision ID: aff58f55852c
Revises: c0f5e8607e37
Create Date: 2016-04-01 07:32:07.269433

"""

# revision identifiers, used by Alembic.
revision = 'aff58f55852c'
down_revision = 'c0f5e8607e37'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("register") as batch_op:
        batch_op.drop_column('reveal')
        batch_op.add_column(sa.Column('expired_on', sa.Date(), nullable=True))

    op.create_index('migration_register_id_ix', 'migration_status', ['register_id'])
    op.create_index('register_details_amends_ix', 'register_details', ['amends'])
    op.create_index('register_cancelled_ix', 'register_details', ['cancelled_by'])
    op.create_index('register_number_ix', 'register', ['registration_no'])
    op.create_index('register_date_ix', 'register', ['date'])


def downgrade():
    with op.batch_alter_table("register") as batch_op:
        batch_op.add_column(sa.Column('reveal', sa.Boolean(), nullable=True))
        batch_op.drop_column('expired_on')

    op.drop_index('migration_register_id_ix')
    op.drop_index('register_details_amends_ix')
    op.drop_index('register_cancelled_ix')
    op.drop_index('register_number_ix')
    op.drop_index('register_date_ix')
