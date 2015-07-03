"""new table

Revision ID: 4166aee97e
Revises: 3caf1276395
Create Date: 2015-07-02 15:15:46.387607

"""

# revision identifiers, used by Alembic.
revision = '4166aee97e'
down_revision = '3caf1276395'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('temp',
                  sa.Column('forename', sa.Unicode())
                  )

    op.add_column('temp',
                  sa.Column('surname', sa.Unicode())
                  )
    pass


def downgrade():
    op.drop_column('temp',
                   'forename')

    op.drop_column('temp',
                   'surname')

    pass
