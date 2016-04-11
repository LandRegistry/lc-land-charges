"""Another index

Revision ID: 3d5f3d61ec72
Revises: aff58f55852c
Create Date: 2016-04-10 15:12:35.648526

"""

# revision identifiers, used by Alembic.
revision = '3d5f3d61ec72'
down_revision = 'aff58f55852c'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index('index_regno_date', 'register', ['registration_no', 'date'])


def downgrade():
    op.drop_index('index_regno_date')
