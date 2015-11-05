"""add search result col

Revision ID: 47d34ea73ec
Revises: 3b752d85780
Create Date: 2015-11-04 14:38:38.610261

"""

# revision identifiers, used by Alembic.
revision = '47d34ea73ec'
down_revision = '3b752d85780'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    with op.batch_alter_table("search_details") as batch_op:
        batch_op.add_column(sa.Column('result', postgresql.JSON(), nullable=True))
    pass


def downgrade():
    with op.batch_alter_table("search_details") as batch_op:
        batch_op.drop_column('result')
    pass
