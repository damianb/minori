''' albums endpoints '''
# pylint: disable=singleton-comparison

from datetime import datetime
import json
import math
from pathlib import Path
from typing import Any, Annotated, Optional, Sequence
import zipfile

import aiofiles.os as aio_os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from natsort import natsorted
import shortuuid
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool

import minori.api_models as models
from minori.core_config import FRONTEND_BASE_FQDN, IMAGE_BASE_FQDN, IMAGE_UPLOAD_PATH, IMAGE_THUMBNAIL_PATH, MINORI_VERSION, TEMP_PATH
from minori.db.connection import AsyncSession
from minori.db.models import Album, Author, AuthorAlias, Image
from minori.util import save_thumbnail
from minori.logger import logger

router = APIRouter(tags=['albums'])

@router.get('/api/albums')
async def get_albums(db: AsyncSession, page: int = 1, include_disabled: bool = False) -> models.PaginatedFullAlbumsResponseModel:
    ''' List all albums (excluding disabled by default) '''

    page = max((page, 1))
    limit = 16
    offset = (page - 1) * limit

    stmt = select(Album)

    if include_disabled is False:
        stmt = stmt.where(Album.disabled == False)

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
        stmt = stmt.where(Album.disabled == False)
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

@router.get('/api/albums/all')
async def get_all_albums(db: AsyncSession, include_disabled: bool = False) -> models.AlbumsResponseModel:
    ''' List all albums without covers (excluding disabled by default) '''

    stmt = select(Album)

    if include_disabled is False:
        stmt = stmt.where(Album.disabled == False)

    stmt = stmt.options(selectinload(Album.author_alias).joinedload(AuthorAlias.author))
    stmt = stmt.order_by(Album.title.asc())
    albums: Sequence[Album] = (await db.execute(stmt)).scalars().all()
    albums = natsorted(albums, key=lambda album: album.title)

    return models.AlbumsResponseModel(
        albums=[album.to_model(include_author_alias=True) for album in albums],
    )

@router.post('/api/albums/-/create')
async def create_album(db: AsyncSession, album: models.CreateAlbumRequestModel) -> models.AlbumResponseModel:
    ''' Create a new album '''

    author_name = album.author or 'Unknown author'
    stmt = select(AuthorAlias).where(AuthorAlias.name == author_name)
    author_alias: Optional[AuthorAlias] = (await db.execute(stmt)).scalars().first()

    if author_alias is None:
        new_author = Author(name=author_name)
        new_author_alias = AuthorAlias(name=author_name, author=new_author)

        db.add(new_author)
        db.add(new_author_alias)

        author_alias = new_author_alias

    new_album = Album(
        title=album.title,
        description=album.description,
        url=album.url,
        created_at=datetime.now(),
        author_alias=author_alias
    )

    db.add(new_album)

    await db.commit()
    await db.refresh(new_album)

    return models.AlbumResponseModel(
        album=new_album.to_model()
    )

@router.get('/api/albums/{album_id}')
async def get_album(db: AsyncSession, album_id: str) -> models.FullAlbumResponseModel:
    ''' Get an album '''

    stmt = select(Album).where(
        Album.uuid == album_id
    ).options(
        selectinload(Album.album_cover),
        selectinload(Album.author_alias).joinedload(AuthorAlias.author),
        selectinload(Album.tags)
    )
    album: Album | None = (await db.execute(stmt)).scalars().first()

    if album is None:
        raise HTTPException(404, 'Album not found.')

    return models.FullAlbumResponseModel(
        album=album.to_full_model()
    )

@router.patch('/api/albums/{album_id}')
async def update_album(db: AsyncSession, album_id: str, album_data: models.UpdateAlbumRequestModel) -> models.AlbumResponseModel:
    ''' Update album metadata '''

    stmt = select(Album).where(
        Album.uuid == album_id
    ).options(selectinload(Album.author_alias).joinedload(AuthorAlias.author))
    album: Album | None = (await db.execute(stmt)).scalars().first()

    if album is None:
        raise HTTPException(404, 'Album not found.')

    if album_data.author is not None:
        author_name = album_data.author or 'Unknown author'
        stmt = select(AuthorAlias).where(AuthorAlias.name == author_name)
        author_alias: Optional[AuthorAlias] = (await db.execute(stmt)).scalars().first()

        if author_alias is None:
            new_author = Author(name=author_name)
            db.add(new_author)

            await db.commit()

            new_author_alias = AuthorAlias(name=author_name, author=new_author)
            db.add(new_author_alias)

            author_alias = new_author_alias

            await db.commit()

        album.author_alias_id = author_alias.id

    if album_data.title is not None:
        album.title = album_data.title

    if album_data.description is not None:
        album.description = album_data.description

    if album_data.url is not None:
        album.url = album_data.url

    await db.commit()
    await db.refresh(album)

    return models.AlbumResponseModel(
        album=album.to_model(include_author_alias=True) # type: ignore
    )

@router.delete('/api/albums/{album_id}')
async def delete_album(db: AsyncSession, album_id: str) -> models.OperationResultModel:
    ''' Delete an album (if disabled) '''

    stmt = select(Album).where(
        Album.uuid == album_id
    ).options(selectinload(Album.images))
    album: Album | None = (await db.execute(stmt)).scalars().first()

    if album is None:
        raise HTTPException(404, 'Album not found.')

    if album.disabled == False:
        raise HTTPException(403, 'Album not disabled, cannot delete.')

    # need to empty out the album cover reference, otherwise sqlalchemy explodes on the delete due to circular references
    album.album_cover = None
    await db.commit()

    for image in album.images:
        if image.uploaded == True and image.filename:
            image_file: Path = IMAGE_UPLOAD_PATH / image.filename
            thumbnail_file: Path = IMAGE_THUMBNAIL_PATH / image.filename
            if await aio_os.path.exists(image_file):
                await aio_os.unlink(image_file)

            if await aio_os.path.exists(thumbnail_file):
                await aio_os.unlink(thumbnail_file)

    await db.delete(album)
    await db.commit()

    return models.OperationResultModel(
        success=True
    )

@router.post('/api/albums/{album_id}/toggle')
async def toggle_album_enabled(db: AsyncSession, album_id: str, state: Optional[bool] = None) -> models.AlbumResponseModel:
    ''' Update an album's enabled/disabled state '''

    stmt = select(Album).where(Album.uuid == album_id)
    album: Album | None = (await db.execute(stmt)).scalars().first()

    if album is None:
        raise HTTPException(404, 'Album not found.')

    if state is None:
        album.disabled = not album.disabled
    else:
        album.disabled = state

    await db.commit()

    return models.AlbumResponseModel(
        album=album.to_model()
    )

@router.post('/api/albums/{album_id}/regen-thumbnails')
async def regenerate_album_image_thumbnails(db: AsyncSession, album_id: str) -> models.OperationResultModel:
    ''' Regenerate all album image thumbnails '''

    stmt = select(Album).where(Album.uuid == album_id)
    album: Album | None = (await db.execute(stmt)).scalars().first()

    if album is None:
        raise HTTPException(404, 'Album not found.')

    stmt = select(Image).where(
        Image.album_id == album.id
    )
    images: Sequence[Image] = (await db.execute(stmt)).scalars().all()

    for image in images:
        if not image.uploaded or not image.filename:
            logger.warning('Skipping image thumbnail regeneration, no image uploaded')
            continue

        await run_in_threadpool(save_thumbnail, (IMAGE_UPLOAD_PATH / image.filename), image.uuid[0:3], image.filename)

    return models.OperationResultModel(
        success=True
    )

async def temp_file_handle():
    ''' Create (and in the event of failure, clean up after) a temp file '''
    tempfile = TEMP_PATH / shortuuid.uuid()
    try:
        yield tempfile
    except: # pylint: disable=bare-except
        try:
            await aio_os.unlink(tempfile.as_posix())
        except: # pylint: disable=bare-except
            pass
        raise

def temp_file_cleanup(temp_file: Path):
    ''' another cleanup routine, because fastapi is awful at this kind of thing '''
    temp_file.unlink(missing_ok=True)

@router.get('/api/albums/{album_id}/download')
async def download_album_as_cbz(
    db: AsyncSession,
    album_id: str,
    temp_file: Annotated[Path, Depends(temp_file_handle)]
    ) -> FileResponse:
    ''' Serve the album itself as a single cbz archive '''

    stmt = select(Album).where(
        Album.uuid == album_id
    ).options(
        selectinload(Album.album_cover),
        selectinload(Album.author_alias).joinedload(AuthorAlias.author),
        selectinload(Album.tags)
    )
    album: Album | None = (await db.execute(stmt)).scalars().first()

    if album is None:
        raise HTTPException(404, 'Album not found.')

    stmt = select(Image).where(
        Image.album_id == album.id
    ).order_by(Image.album_order_key.asc(), Image.original_filename.asc())
    images: Sequence[Image] = (await db.execute(stmt)).scalars().all()

    album_cover_file = Path(album.album_cover.filename) if album.album_cover and album.album_cover.filename else False

    # build info.json file contents:
    info: dict[str, Any] = {
        'id': album.uuid,
        'title': album.title,
        'url': f'/album.html#{album.uuid}',
        'public_url': f'{FRONTEND_BASE_FQDN}/album.html#{album.uuid}',
        'author': album.author_alias.author.name if album.author_alias else '',
        'cover': f'{IMAGE_BASE_FQDN}/thumbs/{album_cover_file.as_posix()}' if album_cover_file else '',
        'rating': -1,
        'source': 'minori',
        'tags': [{'key': tag.to_string().replace(' ', '-'), 'title': tag.to_string() } for tag in album.tags],
        'chapters': {
            album.uuid: {
                'number': 1,
                'volume': 0,
                'url': f'/album.html#{album.uuid}',
                'name': album.title,
                'uploadDate': 0,
                'branch': 'english',
                'entries': '00000000_\\d{6}'
            }
        },
        'app_id': 'minori',
        'app_version': ''.join(MINORI_VERSION.split('.')),
        'cover_entry': ''
    }

    def build_zip():
        ''' Build the actual zip '''

        with zipfile.ZipFile(temp_file, 'x', compression=zipfile.ZIP_DEFLATED) as zfd:
            i = 0
            for image in images:
                if image.filename:
                    image_path = IMAGE_UPLOAD_PATH / image.filename
                    arc_name = f'00000000_{i:06}{image_path.suffix}'
                    zfd.write(image_path, arc_name)
                    if album.album_cover and album.album_cover.id == image.id:
                        info['cover_entry'] = arc_name
                    i += 1

            zfd.writestr('index.json', json.dumps(info))

    await run_in_threadpool(build_zip)

    # whatever brainlet that decided starlette should call a MIMEtype argument "media_type" needs to be slapped
    return FileResponse(
        temp_file,
        filename=f'{album.uuid}.cbz',
        media_type='application/vnd.comicbook+zip',
        background=BackgroundTask(temp_file_cleanup, temp_file)
    )
