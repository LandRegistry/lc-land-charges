"""Add county link to register

Revision ID: 5b8ac27d8ad2
Revises: 2eab7565515c
Create Date: 2016-01-26 10:40:50.065020

"""

# revision identifiers, used by Alembic.
revision = '5b8ac27d8ad2'
down_revision = '2eab7565515c'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("register") as batch_op:
        batch_op.add_column(sa.Column('county_id', sa.Integer(), sa.ForeignKey("county.id"), nullable=True))


def downgrade():
    with op.batch_alter_table("register") as batch_op:
        batch_op.drop_column('county_id')
