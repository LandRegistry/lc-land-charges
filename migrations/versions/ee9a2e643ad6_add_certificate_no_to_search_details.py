"""add certificate_no to search_details

Revision ID: ee9a2e643ad6
Revises: ea44a75b0214
Create Date: 2016-03-10 15:10:45.714681

"""

# revision identifiers, used by Alembic.
revision = 'ee9a2e643ad6'
down_revision = 'ea44a75b0214'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():

    with op.batch_alter_table("search_details") as batch_op:

        batch_op.add_column(sa.Column('certificate_no', sa.Unicode()))

    pass


def downgrade():

    with op.batch_alter_table("search_details") as batch_op:

        batch_op.drop_column('certificate_no')

    pass
