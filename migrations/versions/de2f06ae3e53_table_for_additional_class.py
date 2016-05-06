"""Table for additional Class

Revision ID: de2f06ae3e53
Revises: adb741c9ee25
Create Date: 2016-05-04 10:30:24.170547

"""

# revision identifiers, used by Alembic.
revision = 'de2f06ae3e53'
down_revision = 'adb741c9ee25'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('addl_class_of_charge',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('number', sa.Integer(), nullable=False),
                    sa.Column('orig_number', sa.String(), nullable=True),
                    sa.Column('date', sa.Date(), nullable=True),
                    sa.Column('class_of_charge', sa.String(), nullable=True),
                    )
    op.create_index('ix_addl_class_numberdate', 'addl_class_of_charge', ['number', 'date'])
    op.create_index('ix_addl_class_orig_number', 'addl_class_of_charge', ['orig_number', 'date'])


def downgrade():
    op.drop_table('addl_class_of_charge')