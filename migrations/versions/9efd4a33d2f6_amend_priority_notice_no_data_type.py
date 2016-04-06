"""amend priority notice no data type


Revision ID: 9efd4a33d2f6
Revises: 3aea672f06a9
Create Date: 2016-02-19 07:58:49.700212

"""

# revision identifiers, used by Alembic.
revision = '9efd4a33d2f6'
down_revision = '3aea672f06a9'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute('alter table register_details drop column priority_notice_no')

    with op.batch_alter_table("register_details") as batch_op:
        batch_op.add_column(sa.Column('priority_notice_no', sa.Unicode()))


def downgrade():
    pass
