# pylint: skip-file
"""Mandating the author alias

Revision ID: eb15233fcb26
Revises: 032f7dabb202
Create Date: 2024-10-15 16:03:31.247295

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'eb15233fcb26'
down_revision: Union[str, None] = '032f7dabb202'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('album', 'author_alias_id', existing_type=mysql.INTEGER(display_width=11), nullable=False)


def downgrade() -> None:
    op.alter_column('album', 'author_alias_id', existing_type=mysql.INTEGER(display_width=11), nullable=True)
