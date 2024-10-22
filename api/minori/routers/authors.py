''' authors endpoints '''
# pylint: disable=singleton-comparison

import math
from typing import Sequence

from fastapi import APIRouter, HTTPException
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from minori.db.connection import AsyncSession
from minori.db.models import Album, Author, AuthorAlias
import minori.api_models as models
from minori.logger import logger

router = APIRouter(tags=['authors'])

@router.get('/api/authors')
async def get_authors(db: AsyncSession, page: int = 1) -> models.PaginatedAuthorsResponseModel:
    ''' List all authors '''

    page = max((page, 1))
    limit = 50
    offset = (page - 1) * limit

    stmt = select(Author).order_by(Author.name.desc()).limit(limit).offset(offset)
    authors: Sequence[Author] = (await db.execute(stmt)).scalars().all()

    stmt = select(func.count('*')).select_from(Author) # type: ignore # pylint: disable=not-callable
    (total_records): int = (await db.execute(stmt)).scalars().first() # type: ignore

    total_pages = math.ceil(total_records / limit)

    return models.PaginatedAuthorsResponseModel(
        authors=[author.to_model() for author in authors],
        pagination=models.PaginationModel(
            first_page=1,
            previous_page=(False if page <= 1 else (page - 1)), # pylint: disable=superfluous-parens
            current_page=page,
            next_page=(False if page >= total_pages else (page + 1)), # pylint: disable=superfluous-parens
            last_page=total_pages,
            total_records=total_records
        )
    )

@router.get('/api/authors/{author_id}')
async def get_author(db: AsyncSession, author_id: str) -> models.FullAuthorResponseModel:
    ''' Get an author '''

    stmt = select(Author).where(Author.uuid == author_id).options(selectinload(Author.author_aliases))
    author: Author | None = (await db.execute(stmt)).scalars().first()

    if author is None:
        raise HTTPException(404, 'Author not found.')

    return models.FullAuthorResponseModel(
        author=author.to_full_model()
    )

@router.patch('/api/authors/{author_id}')
async def patch_author_name(
    db: AsyncSession,
    author_id: str,
    author_input: models.UpdateAuthorRequestModel,
    update_corresponding_authoralias: bool = True
    ) -> models.AuthorResponseModel:
    ''' Update the name used by an author (and optionally update its matching AuthorAlias) '''

    stmt = select(Author).where(Author.uuid == author_id)
    author: Author | None = (await db.execute(stmt)).scalars().first()

    if author is None:
        raise HTTPException(404, 'Author not found.')

    author.name = author_input.name

    if update_corresponding_authoralias:
        stmt = select(AuthorAlias).where(
            and_(
                AuthorAlias.author_id == author.id,
                AuthorAlias.name == author.name
            )
        )
        author_alias: AuthorAlias | None = (await db.execute(stmt)).scalars().first()

        if author_alias is not None:
            author_alias.name = author_input.name

    await db.commit()

    return models.AuthorResponseModel(
        author=author.to_model()
    )

@router.delete('/api/authors/{author_id}')
async def delete_author(db: AsyncSession, author_id: str) -> models.OperationResultModel:
    ''' Deletes an author (ONLY if it no longer has child author aliases attached)'''

    stmt = select(Author).where(Author.uuid == author_id).options(selectinload(Author.author_aliases))
    author: Author | None = (await db.execute(stmt)).scalars().first()

    if author is None:
        raise HTTPException(404, 'Author not found.')

    if len(author.author_aliases) > 0:
        raise HTTPException(400, 'Cannot delete; still has attached author aliases.')

    await db.delete(author)
    await db.commit()

    return models.OperationResultModel(
        success=True
    )

@router.get('/api/authors/{author_id}/aliases')
async def get_author_aliases(db: AsyncSession, author_id: str) -> models.AuthorAliasesResponseModel:
    ''' Get an author's associated aliases '''

    stmt = select(Author).where(Author.uuid == author_id).options(selectinload(Author.author_aliases))
    author: Author | None = (await db.execute(stmt)).scalars().first()

    if author is None:
        raise HTTPException(404, 'Author not found.')

    return models.AuthorAliasesResponseModel(
        author_aliases=[author_alias.to_model() for author_alias in author.author_aliases]
    )

@router.get('/api/authors/{author_id}/albums')
async def get_author_albums(db: AsyncSession, author_id: str, page: int = 1, include_disabled: bool = False) -> models.PaginatedFullAlbumsResponseModel:
    ''' List all albums by this author '''

    page = max((page, 1))
    limit = 16
    offset = (page - 1) * limit

    stmt = select(Author).where(Author.uuid == author_id).options(selectinload(Author.author_aliases))
    author: Author | None = (await db.execute(stmt)).scalars().first()

    if author is None:
        raise HTTPException(404, 'Author not found.')

    author_alias_ids: list[int] = [author_alias.id for author_alias in author.author_aliases]

    stmt = select(Album)

    if include_disabled is False:
        stmt = stmt.where(and_(
            Album.author_alias_id.in_(author_alias_ids),
            Album.disabled == False
        ))
    else:
        stmt = stmt.where(Album.author_alias_id.in_(author_alias_ids))

    stmt = stmt.order_by(Album.created_at.desc())
    stmt = stmt.limit(limit).offset(offset)
    stmt = stmt.options(
        selectinload(Album.album_cover),
        selectinload(Album.author_alias).joinedload(AuthorAlias.author),
        selectinload(Album.tags)
    )
    albums: Sequence[Album] = (await db.execute(stmt)).scalars().all()

    # pyright, it's a select count, THE TYPES DON'T WORK LIKE THAT, IT'S NOT GOING TO BE NONE
    # and pylint, you shut up, func.count is in fact callable.
    stmt = select(func.count('*')).select_from(Album) # type: ignore # pylint: disable=not-callable

    if include_disabled is False:
        stmt = stmt.where(and_(
            Album.author_alias_id.in_(author_alias_ids),
            Album.disabled == False
        ))
    else:
        stmt = stmt.where(Album.author_alias_id.in_(author_alias_ids))
    (total_records): int = (await db.execute(stmt)).scalars().first() # type: ignore

    total_pages = math.ceil(total_records / limit)

    return models.PaginatedFullAlbumsResponseModel(
        albums=[album.to_full_model() for album in albums],
        pagination=models.PaginationModel(
            first_page=1,
            previous_page=(False if page <= 1 else (page - 1)), # pylint: disable=superfluous-parens
            current_page=page,
            next_page=(False if page >= total_pages else (page + 1)), # pylint: disable=superfluous-parens
            last_page=total_pages,
            total_records=total_records
        )
    )

@router.post('/api/authors/{author_id}/merge/{consumed_author_id}')
async def merge_author_into_author(
    db: AsyncSession,
    author_id: str,
    consumed_author_id: str,
    preserve_consumed_author: bool = False
    ) -> models.OperationResultModel:
    ''' Merges one author (all of its aliases) to another '''

    stmt = select(Author).where(Author.uuid == author_id).options(selectinload(Author.author_aliases))
    author: Author | None = (await db.execute(stmt)).scalars().first()

    if author is None:
        raise HTTPException(404, 'Author not found.')

    stmt = select(Author).where(Author.uuid == consumed_author_id).options(selectinload(Author.author_aliases))
    consumed_author: Author | None = (await db.execute(stmt)).scalars().first()

    if consumed_author is None:
        raise HTTPException(404, 'Author for consumption not found.')

    logger.warning('test1')
    logger.warning(author.id)

    for author_alias in consumed_author.author_aliases:
        author_alias.author_id = author.id

    logger.warning('test2')

    await db.commit()
    await db.refresh(consumed_author)

    if not preserve_consumed_author:
        await db.delete(consumed_author)

    await db.commit()

    return models.OperationResultModel(
        success=True
    )
