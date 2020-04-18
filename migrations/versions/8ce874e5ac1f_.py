"""empty message

Revision ID: 8ce874e5ac1f
Revises: b07fb22529e1
Create Date: 2020-04-17 17:27:18.320912

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8ce874e5ac1f'
down_revision = 'b07fb22529e1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Module',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('number', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('exercise', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('Submodules',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('number', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('belongs_to', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Submodules')
    op.drop_table('Module')
    # ### end Alembic commands ###