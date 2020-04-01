"""empty message

Revision ID: 2c95843a27c8
Revises: a4f390c12b5a
Create Date: 2020-04-01 01:13:30.109610

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2c95843a27c8'
down_revision = 'a4f390c12b5a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'dob')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('dob', sa.INTEGER(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
