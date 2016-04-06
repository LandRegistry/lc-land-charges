"""Stringy original regn no

Revision ID: a906fae12e18
Revises: ee9a2e643ad6
Create Date: 2016-03-15 08:37:26.332622

"""

# revision identifiers, used by Alembic.
revision = 'a906fae12e18'
down_revision = 'ee9a2e643ad6'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("migration_status") as batch_op:
        batch_op.drop_column('original_regn_no')
        batch_op.add_column(sa.Column('original_regn_no', sa.Unicode()))


def downgrade():
    with op.batch_alter_table("register") as batch_op:
        batch_op.drop_column('original_regn_no')
        batch_op.add_column(sa.Column('original_regn_no', sa.Integer()))
