"""add name id to search results

Revision ID: b9a5a1737bcc
Revises: 5b8ac27d8ad2
Create Date: 2016-01-27 08:45:12.518703

"""

# revision identifiers, used by Alembic.
revision = 'b9a5a1737bcc'
down_revision = '5b8ac27d8ad2'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("search_results") as batch_op:
        batch_op.add_column(sa.Column('name_id', sa.Integer(), sa.ForeignKey('search_name.id')))


def downgrade():
    with op.batch_alter_table("search_results") as batch_op:
        batch_op.drop_column('name_id')