"""Create temporary initial version

Revision ID: 2310e11a851
Revises: 
Create Date: 2015-07-01 07:42:51.837641

"""

# revision identifiers, used by Alembic.
revision = '2310e11a851'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.create_table('temp',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('banks', postgresql.JSON(), nullable=False))


def downgrade():
    op.drop_table('temp')
