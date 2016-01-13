"""welsh added to county

Revision ID: 8fce771da962
Revises: 9f289c415889
Create Date: 2016-01-13 11:54:22.113546

"""

# revision identifiers, used by Alembic.
revision = '8fce771da962'
down_revision = '9f289c415889'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table("county") as batch_op:
        batch_op.add_column(sa.Column('welsh_name', sa.Unicode()))


def downgrade():
    with op.batch_alter_table("county") as batch_op:
        batch_op.drop_column('welsh_name')
