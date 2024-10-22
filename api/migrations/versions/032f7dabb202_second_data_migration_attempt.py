# pylint: skip-file
"""Second data migration attempt

Revision ID: 032f7dabb202
Revises: caf68ff29f0a
Create Date: 2024-10-10 14:54:11.847794

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '032f7dabb202'
down_revision: Union[str, None] = 'caf68ff29f0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    album = sa.sql.table('album',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=32), nullable=False),
        sa.Column('disabled', sa.Boolean(), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('author', sa.String(length=128), nullable=False),
        sa.Column('author_alias_id', sa.Integer(), nullable=True),
        sa.Column('url', sa.String(length=2048), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('album_cover_id', sa.Integer(), nullable=True)
    )
    author = sa.sql.table('author',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False)
    )
    author_alias = sa.sql.table('authoralias',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False)
    )
    conn = op.get_bind()
    res = conn.execute(sa.select(album).where(album.c.author_alias_id == None)) # type: ignore
    results: dict[str, list[int]] = {}
    for r in res.all():
        if r[4] not in results:
            results[r[4]] = [r[0]]
        else:
            results[r[4]] += [r[0]]

    res = conn.execute(sa.select(author_alias))
    author_alias_map: dict[str, int] = {r[2]: r[0] for r in res.all()}

    for author_name, albums_affected in results.items():
        author_alias_id = author_alias_map[author_name]
        conn.execute(
            sa.update(album)
                .where(album.c.id.in_(albums_affected))
                .values({'author_alias_id': author_alias_id})
        )

def downgrade() -> None:
    pass
