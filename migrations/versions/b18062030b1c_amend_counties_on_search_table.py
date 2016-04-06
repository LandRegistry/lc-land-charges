"""amend counties on search table

Revision ID: b18062030b1c
Revises: 66077ce42e4e
Create Date: 2016-02-02 08:40:45.323213

"""

# revision identifiers, used by Alembic.
revision = 'b18062030b1c'
down_revision = '66077ce42e4e'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute('alter table search_details alter column counties type JSON USING counties::JSON')


def downgrade():
    pass
