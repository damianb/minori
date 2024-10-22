''' images endpoints '''
# pylint: disable=singleton-comparison

from datetime import datetime
import json
import os
from pathlib import Path
import re
from typing import Any, Optional, Sequence

import aiofiles
import aiofiles.os as aio_os
from fastapi import APIRouter, HTTPException, UploadFile
import shortuuid
from sqlalchemy import select, and_
from starlette.concurrency import run_in_threadpool

import minori.api_models as models
from minori.core_config import IMAGE_UPLOAD_PATH, IMAGE_THUMBNAIL_PATH, TEMP_PATH
from minori.db.connection import AsyncSession
from minori.db.models import Album, Author, AuthorAlias, Image
from minori.util import extract_zip, process_image, save_thumbnail
from minori.logger import logger

router = APIRouter(tags=['images'])

@router.get('/api/albums/{album_id}/images')
async def get_album_images(db: AsyncSession, album_id: str) -> models.ImagesResponseModel:
    ''' List all images associated with album '''

    stmt = select(Album).where(Album.uuid == album_id)
    album: Album | None = (await db.execute(stmt)).scalars().first()

    if album is None:
        raise HTTPException(404, 'Album not found.')

    stmt = select(Image).where(
        Image.album_id == album.id
    ).order_by(Image.album_order_key.asc(), Image.original_filename.asc())
    images: Sequence[Image] = (await db.execute(stmt)).scalars().all()

    return models.ImagesResponseModel(
        images=[image.to_model() for image in images]
    )

@router.post('/api/albums/{album_id}/images/-/create')
async def create_album_image(db: AsyncSession, album_id: str) -> models.ImageResponseModel:
    ''' Create a new image associated with an album '''

    stmt = select(Album).where(Album.uuid == album_id)
    album: Album | None = (await db.execute(stmt)).scalars().first()

    if album is None:
        raise HTTPException(404, 'Album not found.')

    new_image = Image(
        uploaded=False,
        created_at=datetime.now(),
        album=album
    )

    db.add(new_image)

    await db.commit()
    await db.refresh(new_image)

    return models.ImageResponseModel(
        image=new_image.to_model()
    )

@router.post('/api/albums/{album_id}/images/-/bulkcreate')
async def create_album_images_from_archive(db: AsyncSession, album_id: str, file: UploadFile) -> models.ImagesResponseModel: # pylint: disable=too-many-locals,too-many-branches
    ''' Bulk create album images in response to an uploaded zip archive or cbz archive '''

    stmt = select(Album).where(Album.uuid == album_id)
    album: Album | None = (await db.execute(stmt)).scalars().first()

    if album is None:
        raise HTTPException(404, 'Album not found.')

    uploaded_zip: Path = TEMP_PATH / album.uuid
    temp_images_dir: Path = TEMP_PATH / f'{album.uuid}_files'
    files: list[Path] = []
    new_images: list[Image] = []

    is_cbz_file: bool = (os.path.splitext(file.filename)[-1].lower() == '.cbz') if file.filename else False

    new_album_cover: Optional[Image] = None
    await aio_os.mkdir(temp_images_dir)
    try:
        async with aiofiles.open(uploaded_zip, 'wb') as zfd:
            await zfd.write(file.file.read())

        files = await run_in_threadpool(extract_zip, uploaded_zip, temp_images_dir)

        filename_prefix: str = ''
        cover_entry: Optional[str] = None
        if is_cbz_file:
            if index_file := next((_file for _file in files if _file.name == 'index.json'), None):
                with index_file.open('r', encoding='utf-8') as fd:
                    cbz: dict[str, Any] = json.load(fd)
                    if 'public_url' in cbz:
                        album.url = cbz['public_url']
                    if 'author' in cbz:
                        album.author = cbz['author'] # todo: deprecate and remove

                        author_name = cbz['author'] or 'Unknown author'
                        stmt = select(AuthorAlias).where(AuthorAlias.name == author_name)
                        author_alias: Optional[AuthorAlias] = (await db.execute(stmt)).scalars().first()

                        if author_alias is None:
                            new_author = Author(name=author_name)
                            new_author_alias = AuthorAlias(name=author_name, author=new_author)

                            db.add(new_author)
                            db.add(new_author_alias)

                            author_alias = new_author_alias

                        album.author_alias = author_alias
                    if 'title' in cbz:
                        album.title = cbz['title']

                    if 'id' in cbz and 'chapters' in cbz:
                        cbz_id = str(cbz['id'])
                        if cbz_id in cbz['chapters'] and 'entries' in cbz['chapters'][cbz_id]:
                            filename_prefix = re.sub(r'\\d\{\d\}$', '', cbz['chapters'][cbz_id]['entries'])

                    if 'cover_entry' in cbz:
                        cover_entry = cbz['cover_entry']

                    # todo: support tag importing

        for _file in files:
            uuid = shortuuid.uuid()
            result = await run_in_threadpool(process_image, _file, uuid, raise_on_nonimage=False)
            if result == False:
                continue

            if filename_prefix != '' and not re.match(f'^{filename_prefix}', _file.name): # pylint: disable=consider-using-f-string
                continue

            new_image = Image(
                uuid=uuid,
                filename=result,
                original_filename=re.sub(f'^{filename_prefix}', '', _file.name) if filename_prefix != '' else _file.name, # pylint: disable=consider-using-f-string
                uploaded=True,
                created_at=datetime.now(),
                uploaded_at=datetime.now(),
                album=album,
                album_order_key=0
            )

            db.add(new_image)
            new_images.append(new_image)

            if cover_entry and _file.name == cover_entry:
                new_album_cover = new_image

    except Exception as err: # pylint: disable=broad-except
        for new_image in new_images:
            if not new_image.filename:
                continue

            if await aio_os.path.exists(IMAGE_UPLOAD_PATH / new_image.filename):
                await aio_os.unlink(IMAGE_UPLOAD_PATH / new_image.filename)
            if await aio_os.path.exists(IMAGE_THUMBNAIL_PATH / new_image.filename):
                await aio_os.unlink(IMAGE_THUMBNAIL_PATH / new_image.filename)

        logger.error('Archive upload failed')
        logger.exception(err)

        raise HTTPException(500, 'Server error occurred during file upload.') from err
    finally:
        await aio_os.unlink(uploaded_zip.as_posix())
        for _file in files:
            await aio_os.unlink(_file)
        await aio_os.rmdir(temp_images_dir)

    await db.commit()

    if new_album_cover:
        album.album_cover = new_album_cover
    await db.commit()

    # # rip my performance
    # for new_image in new_images:
    #     await db.refresh(new_image)

    return models.ImagesResponseModel(
        images=[new_image.to_model() for new_image in new_images]
    )

@router.get('/api/albums/{album_id}/images/{image_id}')
async def get_album_image(db: AsyncSession, album_id: str, image_id: str) -> models.ImageResponseModel:
    ''' Get an album image's metadata '''

    stmt = select(Album).where(Album.uuid == album_id)
    album: Album | None = (await db.execute(stmt)).scalars().first()

    if album is None:
        raise HTTPException(404, 'Album not found.')

    stmt = select(Image).where(
        and_(
            Image.uuid == image_id,
            Image.album_id == album.id
        )
    )
    image: Image | None = (await db.execute(stmt)).scalars().first()

    if image is None:
        raise HTTPException(404, 'Image not found.')

    return models.ImageResponseModel(
        image=image.to_model()
    )

@router.put('/api/albums/{album_id}/images/{image_id}/upload')
async def upload_album_image(db: AsyncSession, album_id: str, image_id: str, file: UploadFile) -> models.ImageResponseModel:
    ''' Upload an Image's corresponding image file '''

    stmt = select(Album).where(Album.uuid == album_id)
    album: Album | None = (await db.execute(stmt)).scalars().first()

    if album is None:
        raise HTTPException(404, 'Album not found.')

    stmt = select(Image).where(
        and_(
            Image.uuid == image_id,
            Image.album_id == album.id
        )
    )
    image: Image | None = (await db.execute(stmt)).scalars().first()

    if image is None:
        raise HTTPException(404, 'Image not found.')

    image.original_filename = file.filename
    tempfile: Path = TEMP_PATH / image.uuid
    try:
        async with aiofiles.open(tempfile, 'wb') as fd:
            await fd.write(file.file.read())

        result = await run_in_threadpool(process_image, tempfile, image.uuid)
        if result is False:
            raise HTTPException(400, 'Invalid file uploaded.')

        image.filename = result
    except Exception as err: # pylint: disable=broad-except
        logger.error('Image upload failed')
        logger.exception(err)
        raise HTTPException(500, 'Server error occurred during file upload.') from err
    finally:
        await aio_os.unlink(tempfile.as_posix())

    image.uploaded = True
    image.uploaded_at = datetime.now()

    await db.commit()

    return models.ImageResponseModel(
        image=image.to_model()
    )

@router.post('/api/albums/{album_id}/images/{image_id}/order')
async def update_album_image_order(db: AsyncSession, album_id: str, image_id: str, payload: models.UpdateImageOrderRequestModel) -> models.ImageResponseModel:
    ''' Update an album's order key '''

    stmt = select(Album).where(Album.uuid == album_id)
    album: Album | None = (await db.execute(stmt)).scalars().first()

    if album is None:
        raise HTTPException(404, 'Album not found.')

    stmt = select(Image).where(
        and_(
            Image.uuid == image_id,
            Image.album_id == album.id
        )
    )
    image: Image | None = (await db.execute(stmt)).scalars().first()

    if image is None:
        raise HTTPException(404, 'Image not found.')

    image.album_order_key = int(payload.order)

    await db.commit()

    return models.ImageResponseModel(
        image=image.to_model()
    )

@router.post('/api/albums/{album_id}/images/{image_id}/make-cover')
async def mark_album_image_as_cover(db: AsyncSession, album_id: str, image_id: str) -> models.OperationResultModel:
    ''' Mark an album image as the cover for the album '''

    stmt = select(Album).where(Album.uuid == album_id)
    album: Album | None = (await db.execute(stmt)).scalars().first()

    if album is None:
        raise HTTPException(404, 'Album not found.')

    stmt = select(Image).where(
        and_(
            Image.uuid == image_id,
            Image.album_id == album.id
        )
    )
    image: Image | None = (await db.execute(stmt)).scalars().first()

    if image is None:
        raise HTTPException(404, 'Image not found.')

    album.album_cover = image

    await db.commit()

    return models.OperationResultModel(
        success=True
    )

@router.post('/api/albums/{album_id}/images/{image_id}/regen-thumbnail')
async def regenerate_image_thumbnail(db: AsyncSession, album_id: str, image_id: str) -> models.OperationResultModel:
    ''' Regenerate an image's thumbnail '''

    stmt = select(Album).where(Album.uuid == album_id)
    album: Album | None = (await db.execute(stmt)).scalars().first()

    if album is None:
        raise HTTPException(404, 'Album not found.')

    stmt = select(Image).where(
        and_(
            Image.uuid == image_id,
            Image.album_id == album.id
        )
    )
    image: Image | None = (await db.execute(stmt)).scalars().first()

    if image is None:
        raise HTTPException(404, 'Image not found.')

    if not image.uploaded or not image.filename:
        raise HTTPException(400, 'Image not yet uploaded, cannot regenerate thumbnail.')

    await run_in_threadpool(save_thumbnail, (IMAGE_UPLOAD_PATH / image.filename), image.uuid[0:3], image.filename)

    return models.OperationResultModel(
        success=True
    )

@router.delete('/api/albums/{album_id}/images/{image_id}')
async def delete_album_image(db: AsyncSession, album_id: str, image_id: str) -> models.OperationResultModel:
    ''' Delete an album image '''

    stmt = select(Album).where(Album.uuid == album_id)
    album: Album | None = (await db.execute(stmt)).scalars().first()

    if album is None:
        raise HTTPException(404, 'Album not found.')

    stmt = select(Image).where(
        and_(
            Image.uuid == image_id,
            Image.album_id == album.id
        )
    )
    image: Image | None = (await db.execute(stmt)).scalars().first()

    if image is None:
        raise HTTPException(404, 'Image not found.')

    if image.uploaded == True and image.filename:
        image_file: Path = IMAGE_UPLOAD_PATH / image.filename
        thumbnail_file: Path = IMAGE_THUMBNAIL_PATH / image.filename
        if await aio_os.path.exists(image_file):
            await aio_os.unlink(image_file)

        if await aio_os.path.exists(thumbnail_file):
            await aio_os.unlink(thumbnail_file)

    await db.delete(image)
    await db.commit()

    return models.OperationResultModel(
        success=True
    )
