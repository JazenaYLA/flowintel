"""empty message

Revision ID: 6f6b34409b43
Revises: a8992fc217b2
Create Date: 2023-12-07 11:36:04.602019

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6f6b34409b43'
down_revision = 'a8992fc217b2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('task__template__connector__instance',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('template_id', sa.Integer(), nullable=True),
    sa.Column('instance_id', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('task__template__connector__instance', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_task__template__connector__instance_instance_id'), ['instance_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_task__template__connector__instance_template_id'), ['template_id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('task__template__connector__instance', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_task__template__connector__instance_template_id'))
        batch_op.drop_index(batch_op.f('ix_task__template__connector__instance_instance_id'))

    op.drop_table('task__template__connector__instance')
    # ### end Alembic commands ###
