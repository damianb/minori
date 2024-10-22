''' authoraliases endpoints '''
# pylint: disable=singleton-comparison

import math
from typing import Sequence

from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from minori.db.connection import AsyncSession
from minori.db.models import Author, AuthorAlias
import minori.api_models as models

router = APIRouter(tags=['authoraliases'])

@router.get('/api/authoraliases')
async def get_all_author_aliases(db: AsyncSession, page = 1) -> models.PaginatedAuthorAliasesResponseModel:
    ''' Get all author aliases '''

    page = max((page, 1))
    limit = 50
    offset = (page - 1) * limit

    stmt = select(AuthorAlias).order_by(AuthorAlias.name.desc()).limit(limit).offset(offset)
    author_aliases: Sequence[AuthorAlias] = (await db.execute(stmt)).scalars().all()

    stmt = select(func.count('*')).select_from(AuthorAlias) # type: ignore # pylint: disable=not-callable
    (total_records): int = (await db.execute(stmt)).scalars().first() # type: ignore

    total_pages = math.ceil(total_records / limit)

    return models.PaginatedAuthorAliasesResponseModel(
        author_aliases=[author_alias.to_model() for author_alias in author_aliases],
        pagination=models.PaginationModel(
            first_page=1,
            previous_page=(False if page <= 1 else (page - 1)), # pylint: disable=superfluous-parens
            current_page=page,
            next_page=(False if page >= total_pages else (page + 1)), # pylint: disable=superfluous-parens
            last_page=total_pages,
            total_records=total_records
        )
    )

@router.get('/api/authoraliases/{authoralias_id}')
async def get_author_alias(db: AsyncSession, authoralias_id: str) -> models.FullAuthorAliasResponseModel:
    ''' Get an author alias (and its parent author) '''

    stmt = select(AuthorAlias).where(AuthorAlias.uuid == authoralias_id).options(selectinload(AuthorAlias.author))
    author_alias: AuthorAlias | None = (await db.execute(stmt)).scalars().first()

    if author_alias is None:
        raise HTTPException(404, 'Author alias not found.')

    return models.FullAuthorAliasResponseModel(
        author_alias=author_alias.to_full_model()
    )

@router.patch('/api/authoraliases/{authoralias_id}')
async def rename_author_alias(
    db: AsyncSession,
    authoralias_id: str,
    authoralias_input: models.UpdateAuthorAliasRequestModel
    ) -> models.FullAuthorAliasResponseModel:
    ''' Update (rename) the alias - this _WILL NOT_ change the parent author name, unlike the rename op under Author '''

    stmt = select(AuthorAlias).where(AuthorAlias.uuid == authoralias_id).options(selectinload(AuthorAlias.author))
    author_alias: AuthorAlias | None = (await db.execute(stmt)).scalars().first()

    if author_alias is None:
        raise HTTPException(404, 'Author alias not found.')

    author_alias.name = authoralias_input.name

    await db.commit()

    return models.FullAuthorAliasResponseModel(
        author_alias=author_alias.to_full_model()
    )

@router.delete('/api/authoraliases/{authoralias_id}')
async def delete_author_alias(db: AsyncSession, authoralias_id: str) -> models.OperationResultModel:
    ''' Delete the author alias (without deleting the parent author) '''

    stmt = select(AuthorAlias).where(AuthorAlias.uuid == authoralias_id).options(selectinload(AuthorAlias.author))
    author_alias: AuthorAlias | None = (await db.execute(stmt)).scalars().first()

    if author_alias is None:
        raise HTTPException(404, 'Author alias not found.')

    await db.delete(author_alias)

    return models.OperationResultModel(
        success=True
    )

@router.post('/api/authoraliases/{authoralias_id}/reassign/{new_parent_author_id}')
async def reassign_author_alias(db: AsyncSession, authoralias_id: str, new_parent_author_id: str) -> models.FullAuthorAliasResponseModel:
    ''' Reassign the author alias to a new parent author '''

    stmt = select(AuthorAlias).where(AuthorAlias.uuid == authoralias_id).options(selectinload(AuthorAlias.author))
    author_alias: AuthorAlias | None = (await db.execute(stmt)).scalars().first()

    if author_alias is None:
        raise HTTPException(404, 'Author alias not found.')

    stmt = select(Author).where(Author.uuid == new_parent_author_id)
    new_author: Author | None = (await db.execute(stmt)).scalars().first()

    if new_author is None:
        raise HTTPException(404, 'New parent author not found.')

    author_alias.author = new_author
    await db.commit()

    return models.FullAuthorAliasResponseModel(
        author_alias=author_alias.to_full_model()
    )
