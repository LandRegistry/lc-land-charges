"""amendment type

Revision ID: aa3a1cba7cff
Revises: 02587cb3d574
Create Date: 2016-01-22 12:59:26.176985

"""

# revision identifiers, used by Alembic.
revision = 'aa3a1cba7cff'
down_revision = '02587cb3d574'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("register_details") as batch_op:
        batch_op.add_column(sa.Column('amendment_type', sa.Unicode()))


def downgrade():
    with op.batch_alter_table("register_details") as batch_op:
        batch_op.drop_column('amendment_type')
