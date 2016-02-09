"""Reveal or not

Revision ID: dfc488336c94
Revises: 5e3a8927492f
Create Date: 2016-02-08 14:12:53.494143

"""

# revision identifiers, used by Alembic.
revision = 'dfc488336c94'
down_revision = '5e3a8927492f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("register") as batch_op:
        batch_op.add_column(sa.Column('reveal', sa.Boolean(), nullable=False, default=True))


def downgrade():
    with op.batch_alter_table("register") as batch_op:
        batch_op.drop_column('reveal')
