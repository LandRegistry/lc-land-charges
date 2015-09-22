"""Initial County Data

Revision ID: 1aba1e4d285
Revises: 491486b3053
Create Date: 2015-09-22 08:40:13.192038

"""

# revision identifiers, used by Alembic.
revision = '1aba1e4d285'
down_revision = '491486b3053'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('counties',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('welsh_name', sa.String(), nullable=True)
                    )
    # TODO: There's a lot we could do with counties, such as handling historical
    # counties per the Practise Guide.


def downgrade():
    op.drop_table('counties')
