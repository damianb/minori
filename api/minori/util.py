''' utility functions for across the application '''

import os
from pathlib import Path
from typing import Literal
import zipfile

from fastapi import HTTPException
from natsort import natsorted
from PIL import Image as img
import shortuuid

from minori.core_config import ALLOWED_FILE_TYPES, IMAGE_UPLOAD_PATH, IMAGE_THUMBNAIL_PATH, IMAGE_THUMBNAIL_SIZE

def get_env_secret(env_name: str, default: str | None = None) -> str | None:
    ''' Get secrets from env var, preferring _FILE secrets but using directly passed secrets if available '''
    if env_val := os.environ.get(env_name + '_FILE', None):
        return Path(env_val).read_text('utf8').strip()

    if env_val := os.environ.get(env_name, None):
        return env_val

    return default

def extract_zip(uploaded_zip: Path, tempdir: Path):
    ''' Extract a zip file of all images and return a list of all files present '''

    if not zipfile.is_zipfile(uploaded_zip):
        raise HTTPException(400, 'Invalid archive detected.')

    files: list[Path] = []
    with zipfile.ZipFile(uploaded_zip, 'r') as zfd:
        members = zfd.infolist()
        members = natsorted(members, key=lambda member: Path(member.filename).name)

        for member in members:
            destination_file = tempdir / (Path(member.filename).name)
            with open(destination_file, 'wb') as fd:
                fd.write(zfd.read(member))
            files.append(destination_file)

    return files

def process_image(tempfile: Path, image_uuid: str, raise_on_nonimage: bool = True) -> str | Literal[False]:
    ''' Save and generate a thumbnail for a given image (warning: synchronous) '''

    filename: str = ''
    try:
        with img.open(tempfile) as fd:
            fd.verify()
    except Exception as err: # pylint: disable=broad-except
        if raise_on_nonimage is False:
            return False

        raise HTTPException(400, 'Invalid image detected.') from err

    file_type = ''
    with img.open(tempfile) as fd:
        file_type = (fd.format or '').lower()

        if file_type not in ALLOWED_FILE_TYPES:
            if raise_on_nonimage is False:
                return False

            raise HTTPException(400, 'Invalid file type detected.')

    sub_path_slice = image_uuid[0:3]
    filename = f'{sub_path_slice}/{str(shortuuid.decode(image_uuid))}.{file_type}'
    save_image(tempfile, sub_path_slice, filename)
    save_thumbnail(tempfile, sub_path_slice, filename)

    return filename

def save_image(original_file: Path, sub_path_slice: str, filename: str) -> None:
    ''' Save the image to the upload path '''

    with img.open(original_file) as fd:
        (IMAGE_UPLOAD_PATH / sub_path_slice).mkdir(mode=0o775, exist_ok=True)
        image_file_path: Path = IMAGE_UPLOAD_PATH / filename

        if getattr(fd, 'is_animated', False):
            fd.save(image_file_path, save_all=True)
            fd.seek(0)
        else:
            fd.save(image_file_path)

def save_thumbnail(original_file: Path, sub_path_slice: str, filename: str) -> None:
    ''' Generate and save a thumbnail to the thumbnail path '''

    with img.open(original_file) as fd:
        (IMAGE_THUMBNAIL_PATH / sub_path_slice).mkdir(mode=0o775, exist_ok=True)
        thumbnail_file_path: Path = IMAGE_THUMBNAIL_PATH / filename

        if thumbnail_file_path.exists():
            thumbnail_file_path.unlink()

        fd.thumbnail((IMAGE_THUMBNAIL_SIZE, IMAGE_THUMBNAIL_SIZE))
        fd.save(thumbnail_file_path)
