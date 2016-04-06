"""county and postcode columns

Revision ID: 45cada0cf4f
Revises: af34e72534
Create Date: 2015-08-26 11:46:53.190485

"""

# revision identifiers, used by Alembic.
revision = '45cada0cf4f'
down_revision = 'af34e72534'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("address_detail") as batch_op:
        batch_op.add_column(sa.Column('county', sa.Unicode()))
        batch_op.add_column(sa.Column('postcode', sa.Unicode()))


def downgrade():
    with op.batch_alter_table("address_detail") as batch_op:
        batch_op.drop_column('county')
        batch_op.drop_column('postcode')
