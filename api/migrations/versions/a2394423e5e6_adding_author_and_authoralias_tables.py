# pylint: skip-file
"""Adding Author and AuthorAlias tables

Revision ID: a2394423e5e6
Revises: 7d646be4eed8
Create Date: 2024-10-05 23:58:54.294314

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2394423e5e6'
down_revision: Union[str, None] = '7d646be4eed8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('author',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_author')),
        sa.UniqueConstraint('name', name=op.f('uq_author_name')),
        sa.UniqueConstraint('uuid', name=op.f('uq_author_uuid'))
    )
    op.create_table('authoralias',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['author.id'], name=op.f('fk_authoralias_author_id_author')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_authoralias')),
        sa.UniqueConstraint('name', name=op.f('uq_authoralias_name')),
        sa.UniqueConstraint('uuid', name=op.f('uq_authoralias_uuid'))
    )
    op.add_column('album', sa.Column('author_alias_id', sa.Integer(), nullable=True))
    op.create_foreign_key(op.f('fk_album_author_alias_id_authoralias'), 'album', 'authoralias', ['author_alias_id'], ['id'])

def downgrade() -> None:
    op.drop_constraint(op.f('fk_album_author_alias_id_authoralias'), 'album', type_='foreignkey')
    op.drop_column('album', 'author_alias_id')
    op.drop_table('authoralias')
    op.drop_table('author')

