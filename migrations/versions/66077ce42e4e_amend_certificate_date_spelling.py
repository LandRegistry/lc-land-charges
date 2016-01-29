"""amend certificate date spelling

Revision ID: 66077ce42e4e
Revises: d19ded22eaa3
Create Date: 2016-01-29 11:25:07.107718

"""

# revision identifiers, used by Alembic.
revision = '66077ce42e4e'
down_revision = 'd19ded22eaa3'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute('alter table search_details rename column certifcate_date to certificate_date')


def downgrade():
    pass
