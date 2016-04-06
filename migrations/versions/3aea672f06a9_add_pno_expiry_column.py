"""Add PNO expiry column

Revision ID: 3aea672f06a9
Revises: dfc488336c94
Create Date: 2016-02-10 14:04:49.971992

"""

# revision identifiers, used by Alembic.
revision = '3aea672f06a9'
down_revision = 'dfc488336c94'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("register_details") as batch_op:
        batch_op.add_column(sa.Column('prio_notice_expires', sa.Date()))


def downgrade():
    with op.batch_alter_table("register_details") as batch_op:
        batch_op.drop_column('prio_notice_expires')
