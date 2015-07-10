"""New structures for migrated data

Revision ID: 31cae288f4e
Revises: 49d005085d0
Create Date: 2015-07-10 09:58:22.407558

"""

# revision identifiers, used by Alembic.
revision = '31cae288f4e'
down_revision = '49d005085d0'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.create_table('migration_status',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('register_id', sa.Integer(), sa.ForeignKey('register.id'), nullable=False),
                    sa.Column('original_regn_no', sa.Integer()),
                    sa.Column('migration_complete', sa.Boolean, nullable=False, default=False),
                    sa.Column('extra_data', postgresql.JSON()))
    pass


def downgrade():
    op.drop_table('migration_status')
