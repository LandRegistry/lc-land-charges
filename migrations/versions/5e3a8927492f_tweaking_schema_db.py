"""Tweaking schema & db

Revision ID: 5e3a8927492f
Revises: b18062030b1c
Create Date: 2016-02-04 07:52:48.357637

"""

# revision identifiers, used by Alembic.
revision = '5e3a8927492f'
down_revision = 'b18062030b1c'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Using op. was generating nonsense errors and I couldn't see my mistake.
    # Sigh, then just issue the commands.
    op.execute('alter table request drop column document_ref')
    op.execute('alter table register_details drop column registration_date')
    op.execute('alter table register_details drop column legal_body')
    op.execute('alter table address alter column address_type type character varying')


def downgrade():
    with op.batch_alter_table("request") as batch_op:
        batch_op.add_column(sa.Column('document_ref', sa.Unicode()))

    with op.batch_alter_table("register_details") as batch_op:
        batch_op.add_column(sa.Column('registration_date', sa.Date()))
        batch_op.add_column(sa.Column('legal_body', sa.Unicode()))
