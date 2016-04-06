"""search results table added

Revision ID: 118b360dcc04
Revises: ec8ec2a3dea7
Create Date: 2016-01-22 11:23:18.541847

"""

# revision identifiers, used by Alembic.
revision = '118b360dcc04'
down_revision = 'ec8ec2a3dea7'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.create_table('search_results',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('request_id', sa.Integer(), sa.ForeignKey('request.id'), nullable=False),
                    sa.Column('search_details_id', sa.Integer(), sa.ForeignKey('search_details.id'), nullable=False),
                    sa.Column('result', postgresql.JSON(), nullable=True)
                    )


def downgrade():
    op.drop_table('search_results')
