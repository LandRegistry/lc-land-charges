"""complex name and number added

Revision ID: 3b752d85780
Revises: 1aba1e4d285
Create Date: 2015-11-02 10:53:25.146386

"""

# revision identifiers, used by Alembic.
revision = '3b752d85780'
down_revision = '1aba1e4d285'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("party_name") as batch_op:
        batch_op.add_column(sa.Column('complex_number', sa.Integer()))
        batch_op.add_column(sa.Column('complex_name', sa.Unicode()))


def downgrade():
    with op.batch_alter_table("party_name") as batch_op:
        batch_op.drop_column('complex_number')
        batch_op.drop_column('complex_name')
