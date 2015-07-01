"""Load some data

Revision ID: 3caf1276395
Revises: 2310e11a851
Create Date: 2015-07-01 09:45:29.505550

"""

# revision identifiers, used by Alembic.
revision = '3caf1276395'
down_revision = '2310e11a851'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table
import os
import json
from sqlalchemy.dialects import postgresql


def upgrade():
    temptable = table('temp',
                     sa.Column('id', sa.Integer(), primary_key=True),
                     sa.Column('banks', postgresql.JSON(), nullable=False))

    dir = os.path.join(os.path.dirname(__file__), '../data')
    files = [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))]

    data = []
    for file in files:
        if file != ".DS_Store": # Temp MacOS bodge.
            json_dict = json.loads(open(os.path.join(dir, file)).read())
            data.append({'banks': json_dict})
    print(data)
    op.bulk_insert(temptable, data)


def downgrade():
    pass
