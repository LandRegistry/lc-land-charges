"""drop register unique constraint

Revision ID: 604097d02f12
Revises: bc08a3789a93
Create Date: 2016-03-04 15:58:13.568968

"""

# revision identifiers, used by Alembic.
revision = '604097d02f12'
down_revision = 'bc08a3789a93'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_constraint("uq_registration_ref", "register")


def downgrade():
    op.create_unique_constraint("uq_registration_ref", "register", ["registration_no", "date"])