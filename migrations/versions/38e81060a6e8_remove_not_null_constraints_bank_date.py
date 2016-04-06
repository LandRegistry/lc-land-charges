"""remove not-null constraints bank date

Revision ID: 38e81060a6e8
Revises: 02587cb3d574
Create Date: 2016-01-21 08:58:44.387200

"""

# revision identifiers, used by Alembic.
revision = '38e81060a6e8'
down_revision = '02587cb3d574'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute('ALTER TABLE register_details ALTER COLUMN bankruptcy_date DROP NOT NULL')
    pass


def downgrade():
    pass
