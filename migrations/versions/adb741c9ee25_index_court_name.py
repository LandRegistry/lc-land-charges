"""Index court name

Revision ID: adb741c9ee25
Revises: aff58f55852c
Create Date: 2016-04-11 11:14:52.423910

"""

# revision identifiers, used by Alembic.
revision = 'adb741c9ee25'
down_revision = '3d5f3d61ec72'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


def upgrade():
    op.create_index('details_court_upper_ix', 'register_details', [text('upper(legal_body_ref)')])


def downgrade():
    op.drop_index('details_court_upper_ix')
