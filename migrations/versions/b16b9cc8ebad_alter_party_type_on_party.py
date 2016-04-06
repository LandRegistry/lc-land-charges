"""alter party type on party

Revision ID: b16b9cc8ebad
Revises: 8fce771da962
Create Date: 2016-01-15 08:36:24.531887

"""

# revision identifiers, used by Alembic.
revision = 'b16b9cc8ebad'
down_revision = '8fce771da962'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute('alter table party alter column party_type type character varying')


def downgrade():
    pass