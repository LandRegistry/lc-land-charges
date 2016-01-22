"""add priority notice columns

Revision ID: d773e0a1af3d
Revises: 38e81060a6e8
Create Date: 2016-01-21 09:01:51.054592

"""

# revision identifiers, used by Alembic.
revision = 'd773e0a1af3d'
down_revision = '38e81060a6e8'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("register_details") as batch_op:
        batch_op.add_column(sa.Column('priority_notice_ind', sa.Boolean()))
        batch_op.add_column(sa.Column('priority_notice_no', sa.Integer()))


def downgrade():
    with op.batch_alter_table("register_details") as batch_op:
        batch_op.drop_column('priority_notice_ind')
        batch_op.drop_column('priority_notice_no')
