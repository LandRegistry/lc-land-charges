"""Store username in request

Revision ID: dda4b1353f86
Revises: 430aaf9daf50
Create Date: 2016-03-18 14:26:53.829380

"""

# revision identifiers, used by Alembic.
revision = 'dda4b1353f86'
down_revision = '430aaf9daf50'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("request") as batch_op:
        batch_op.add_column(sa.Column('caseworker_uid', sa.Unicode()))


def downgrade():
    with op.batch_alter_table("request") as batch_op:
        batch_op.drop_column('caseworker_uid')
