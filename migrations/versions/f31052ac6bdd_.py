"""empty message

Revision ID: f31052ac6bdd
Revises: 47fda9725699
Create Date: 2020-04-18 02:41:59.365193

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f31052ac6bdd'
down_revision = '47fda9725699'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('submodules', sa.Column('maxelements', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('submodules', 'maxelements')
    # ### end Alembic commands ###
