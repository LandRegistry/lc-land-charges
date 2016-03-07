"""add registration sequence number

Revision ID: bc08a3789a93
Revises: 273e31d6ab30
Create Date: 2016-03-04 15:35:15.138687

"""

# revision identifiers, used by Alembic.
revision = 'bc08a3789a93'
down_revision = '273e31d6ab30'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("register") as batch_op:
        batch_op.add_column(sa.Column('reg_sequence_no', sa.Integer()))


def downgrade():
    with op.batch_alter_table("register") as batch_op:
        batch_op.drop_column('reg_sequence_no')
