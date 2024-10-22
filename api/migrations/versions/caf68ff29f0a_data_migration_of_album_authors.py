# pylint: skip-file
"""Data migration of album authors

Revision ID: caf68ff29f0a
Revises: a2394423e5e6
Create Date: 2024-10-07 21:25:17.283428

"""
from typing import Sequence, Union

from alembic import op
import shortuuid
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'caf68ff29f0a'
down_revision: Union[str, None] = 'a2394423e5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Add any optional data upgrade migrations here!"""
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
    res = conn.execute(sa.select(album)) # type: ignore
    results: dict[str, list[int]] = {}
    for r in res.all():
        if r[1] not in results:
            results[r[4]] = [r[0]]
        else:
            results[r[4]].append(r[0])
    authors = [{
        'uuid': shortuuid.uuid(),
        'name': r
    } for r in results.keys()]

    op.bulk_insert(author, authors)
    res = conn.execute(sa.select(author))
    author_map = {}
    for r in res.all():
        author_map[r[2]] = r[0]
    author_aliases = [{
        'uuid': shortuuid.uuid(),
        'name': author_name,
        'author_id': author_id
    } for author_name, author_id in author_map.items()]
    op.bulk_insert(author_alias, author_aliases)
    res = conn.execute(sa.select(author_alias))
    author_alias_map = {}
    for r in res.all():
        author_alias_map[r[2]] = r[0]
    for author_alias_name, author_alias_id in author_alias_map.items():
        original_albums = results[author_alias_name]
        conn.execute(
            sa.update(album)
                .where(album.c.id.in_(original_albums))
                .values({'author_alias_id': author_alias_id})
        )

def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.sql.text('SET FOREIGN_KEY_CHECKS = 0'))
    conn.execute(sa.sql.text('UPDATE album SET album.author_alias_id = null'))
    conn.execute(sa.sql.text('TRUNCATE TABLE authoralias'))
    conn.execute(sa.sql.text('TRUNCATE TABLE author'))
    conn.execute(sa.sql.text('SET FOREIGN_KEY_CHECKS = 1'))
