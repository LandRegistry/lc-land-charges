"""add searchable name to party name

Revision ID: bed0d82acf15
Revises: b9a5a1737bcc
Create Date: 2016-01-27 16:23:50.566535

"""

# revision identifiers, used by Alembic.
revision = 'bed0d82acf15'
down_revision = 'b9a5a1737bcc'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("party_name") as batch_op:
        batch_op.add_column(sa.Column('searchable_string', sa.Unicode()))


def downgrade():
    with op.batch_alter_table("party_name") as batch_op:
        batch_op.drop_column('searchable_string')