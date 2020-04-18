"""empty message

Revision ID: 28cce562cc4e
Revises: 8ce874e5ac1f
Create Date: 2020-04-17 19:41:13.924029

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '28cce562cc4e'
down_revision = '8ce874e5ac1f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Submodule',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('number', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('belongs_to', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('Submodules')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Submodules',
    sa.Column('id', sa.INTEGER(), server_default=sa.text('nextval(\'"Submodules_id_seq"\'::regclass)'), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('number', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('belongs_to', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='Submodules_pkey')
    )
    op.drop_table('Submodule')
    # ### end Alembic commands ###
