"""Add date to register

Revision ID: 216e3942ea3
Revises: 47d34ea73ec
Create Date: 2015-12-08 08:14:23.564759

"""

# revision identifiers, used by Alembic.
revision = '216e3942ea3'
down_revision = '47d34ea73ec'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("register") as batch_op:
        batch_op.add_column(sa.Column('date', sa.DateTime()))


def downgrade():
    with op.batch_alter_table("register") as batch_op:
        batch_op.drop_column('date')
