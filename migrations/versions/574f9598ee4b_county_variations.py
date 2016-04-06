"""County variations

Revision ID: 574f9598ee4b
Revises: 912538deda35
Create Date: 2016-02-23 13:50:46.029704

"""

# revision identifiers, used by Alembic.
revision = '574f9598ee4b'
down_revision = '912538deda35'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('county_search_keys',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('key', sa.String(), nullable=True),
                    sa.Column('variant_of', sa.String()),
                    sa.Column('county_council', sa.Boolean())
                    )


def downgrade():
    op.drop_table('county_search_keys')
