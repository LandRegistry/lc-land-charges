"""Changes for searches

Revision ID: 491486b3053
Revises: 45cada0cf4f
Create Date: 2015-09-18 09:01:39.201321

"""

# revision identifiers, used by Alembic.
revision = '491486b3053'
down_revision = '45cada0cf4f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    with op.batch_alter_table("request") as batch:
        batch.add_column(sa.Column("customer_name", sa.Unicode()))
        batch.add_column(sa.Column("customer_address", sa.Unicode()))

    op.create_table('search_details',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('request_id', sa.Integer(), sa.ForeignKey('request.id')),
                    sa.Column('parameters', postgresql.JSON(), nullable=False))


def downgrade():
    op.drop_table('search_details')
    with op.batch_alter_table("request") as batch:
        batch.drop_column('customer_address')
        batch.drop_column('customer_name')
