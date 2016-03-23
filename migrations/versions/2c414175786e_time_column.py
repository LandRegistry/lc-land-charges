"""Time column

Revision ID: 2c414175786e
Revises: dda4b1353f86
Create Date: 2016-03-23 11:10:35.691342

"""

# revision identifiers, used by Alembic.
revision = '2c414175786e'
down_revision = 'dda4b1353f86'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("request") as batch_op:
        batch_op.add_column(sa.Column('application_time', sa.Time()))


def downgrade():
    with op.batch_alter_table("request") as batch_op:
        batch_op.drop_column('application_time')
