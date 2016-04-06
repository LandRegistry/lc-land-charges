"""Refine migration status

Revision ID: 2eab7565515c
Revises: aa3a1cba7cff
Create Date: 2016-01-25 09:35:56.517201

"""

# revision identifiers, used by Alembic.
revision = '2eab7565515c'
down_revision = 'aa3a1cba7cff'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute('ALTER TABLE migration_status ALTER COLUMN register_id DROP NOT NULL')
    with op.batch_alter_table("migration_status") as batch_op:
        batch_op.add_column(sa.Column('date', sa.DateTime()))
        batch_op.add_column(sa.Column('class_of_charge', sa.String()))


def downgrade():
    with op.batch_alter_table("migration_status") as batch_op:
        batch_op.drop_column('date')
        batch_op.drop_column('class_of_charge')
