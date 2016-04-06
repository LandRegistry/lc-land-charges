"""More amend details

Revision ID: ea44a75b0214
Revises: 604097d02f12
Create Date: 2016-03-07 15:48:10.912353

"""

# revision identifiers, used by Alembic.
revision = 'ea44a75b0214'
down_revision = '604097d02f12'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("register_details") as batch_op:
        batch_op.add_column(sa.Column('amend_info_details_orig', sa.String()))


def downgrade():
    with op.batch_alter_table("register_details") as batch_op:
        batch_op.drop_column('amend_info_details_orig')
