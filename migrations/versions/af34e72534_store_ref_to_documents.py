"""store ref to documents

Revision ID: af34e72534
Revises: 3784951a9d3
Create Date: 2015-08-25 14:41:47.015872

"""

# revision identifiers, used by Alembic.
revision = 'af34e72534'
down_revision = '3784951a9d3'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("request") as batch_op:
        batch_op.add_column(sa.Column('document_ref', sa.Unicode()))

    with op.batch_alter_table("register_details") as batch_op:
        batch_op.drop_column('cancelled_on')
        batch_op.add_column(sa.Column('cancelled_by', sa.Integer()))


def downgrade():
    with op.batch_alter_table("request") as batch_op:
        batch_op.drop_column('document_ref')

    with op.batch_alter_table("register_details") as batch_op:
        batch_op.drop_column('cancelled_by')
        batch_op.add_column(sa.Column('cancelled_on', sa.DateTime()))