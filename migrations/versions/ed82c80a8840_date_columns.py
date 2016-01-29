"""Date columns

Revision ID: ed82c80a8840
Revises: bed0d82acf15
Create Date: 2016-01-29 09:12:11.301683

"""

# revision identifiers, used by Alembic.
revision = 'ed82c80a8840'
down_revision = 'bed0d82acf15'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa



def upgrade():
    with op.batch_alter_table("search_details") as batch_op:
        batch_op.add_column(sa.Column('certifcate_date', sa.Date()))
        batch_op.add_column(sa.Column('expiry_date', sa.Date()))


def downgrade():
    with op.batch_alter_table("search_details") as batch_op:
        batch_op.drop_column('certifcate_date')
        batch_op.drop_column('expiry_date')