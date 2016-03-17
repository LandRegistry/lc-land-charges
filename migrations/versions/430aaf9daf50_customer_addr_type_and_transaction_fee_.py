"""customer_addr_type and transaction fee added

Revision ID: 430aaf9daf50
Revises: f82a88ad5d9b
Create Date: 2016-03-17 14:28:40.685763

"""

# revision identifiers, used by Alembic.
revision = '430aaf9daf50'
down_revision = 'f82a88ad5d9b'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("request") as batch_op:
        batch_op.add_column(sa.Column('customer_addr_type', sa.Unicode()))
        batch_op.add_column(sa.Column('transaction_fee', sa.Unicode()))


def downgrade():
    with op.batch_alter_table("request") as batch_op:
        batch_op.drop_column('customer_addr_type')
        batch_op.drop_column('transaction_fee')
