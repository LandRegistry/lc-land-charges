"""amend year columns on search

Revision ID: 35dc4dbaff79
Revises: 118b360dcc04
Create Date: 2016-01-22 14:16:08.050769

"""

# revision identifiers, used by Alembic.
revision = '35dc4dbaff79'
down_revision = '118b360dcc04'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute('alter table search_name drop column year_search_from restrict')
    op.execute('alter table search_name drop column year_search_to restrict')
    op.execute('alter table search_name add column year_from integer')
    op.execute('alter table search_name add column year_to integer')


def downgrade():
    pass
