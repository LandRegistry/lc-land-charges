"""Index searchable name

Revision ID: d19ded22eaa3
Revises: ed82c80a8840
Create Date: 2016-01-29 10:21:02.275174

"""

# revision identifiers, used by Alembic.
revision = 'd19ded22eaa3'
down_revision = 'ed82c80a8840'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index('ix_searchname', 'party_name', ['searchable_string'])


def downgrade():
    op.drop_index('ix_searchname')
