"""Changes for amends and cancs

Revision ID: 18e886734a7
Revises: 2e75589aea3
Create Date: 2015-08-21 12:36:32.737866

"""

# revision identifiers, used by Alembic.
revision = '18e886734a7'
down_revision = '2e75589aea3'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("ALTER TABLE register DROP CONSTRAINT IF EXISTS register_registration_no_key")
    with op.batch_alter_table("register_details") as batch_op:
        batch_op.add_column(sa.Column('amends', sa.Integer()))
        batch_op.add_column(sa.Column('cancelled_on', sa.DateTime()))
        # batch_op.add_column(sa.Column('amend_request_id', sa.Integer()))


def downgrade():
    with op.batch_alter_table("register") as batch_op:
        batch_op.create_unique_constraint(None, ['registration_no'])

    with op.batch_alter_table("register_details") as batch_op:
        batch_op.drop_column('amends')
        batch_op.drop_column('cancelled_on')
        # batch_op.drop_column('amend_request_id')
