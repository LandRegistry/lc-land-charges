"""add class of charge to register details

Revision ID: 02587cb3d574
Revises: b16b9cc8ebad
Create Date: 2016-01-15 10:44:41.874983

"""

# revision identifiers, used by Alembic.
revision = '02587cb3d574'
down_revision = 'b16b9cc8ebad'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute('alter table register_details rename column application_type to class_of_charge')


def downgrade():
    pass
