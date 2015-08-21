"""Remove not-null constraints

Revision ID: 2e75589aea3
Revises: 35074826ef3
Create Date: 2015-07-16 10:19:37.975754

"""

# revision identifiers, used by Alembic.
revision = '2e75589aea3'
down_revision = '35074826ef3'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute('ALTER TABLE address ALTER COLUMN detail_id DROP NOT NULL')
    pass


def downgrade():
    #op.execute('ALTER TABLE address ALTER COLUMN detail_id SET NOT NULL')
    pass
