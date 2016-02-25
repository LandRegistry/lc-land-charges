"""name subtype

Revision ID: 273e31d6ab30
Revises: 574f9598ee4b
Create Date: 2016-02-25 08:04:08.672592

"""

# revision identifiers, used by Alembic.
revision = '273e31d6ab30'
down_revision = '574f9598ee4b'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


# This is a bit of a hack - in the case of 'various name types', we'll store whether it's
# an 'A' or a 'B'. This will make the search code easier and save re-implementing the A/B
# decider code in the synchronier
# We like indicator columns
def upgrade():
    with op.batch_alter_table("party_name") as batch_op:
        batch_op.add_column(sa.Column('subtype', sa.String(), nullable=True))


def downgrade():
    with op.batch_alter_table("party_name") as batch_op:
        batch_op.drop_column('subtype')
