#!/usr/bin/env python3
''' minori uploader '''

import argparse
import logging
from pathlib import Path
import sys
import tempfile
from typing import Optional
import zipfile

from natsort import natsorted
import requests

# set up logging configuration - only to stdout/stderr for now
class ErrorLogFilter(logging.Filter):
    ''' prevents error logs from making it into stdout '''
    def __init__(self, name: str = 'ErrorLogFilter') -> None:
        super().__init__(name)

    def filter(self, record):
        return record.levelno < logging.WARNING

logger = logging.getLogger('build')
log_formatter = logging.Formatter(
    '[%(asctime)s] (%(name)s:%(levelname)s) %(message)s',
    '%Y-%m-%dT%H:%M:%S%z'
)

log_stdout_handler = logging.StreamHandler(sys.stdout)
log_stdout_handler.addFilter(ErrorLogFilter())
log_stdout_handler.setFormatter(log_formatter)

log_stderr_handler = logging.StreamHandler(sys.stderr)
log_stderr_handler.setFormatter(log_formatter)
log_stderr_handler.setLevel(logging.WARNING)

logger.addHandler(log_stdout_handler)
logger.addHandler(log_stderr_handler)

logger.setLevel(logging.INFO)

def main( # pylint: disable=too-many-branches
        title: Optional[str],
        author: Optional[str],
        album_file_path: Optional[Path],
        album_dir: Optional[Path],
        minori_api_url: str,
    ) -> None:
    ''' main method '''

    body = {}
    if title:
        body['title'] = title
    if author:
        body['author'] = author

    if (not album_file_path and not album_dir) or (album_file_path and album_dir):
        raise ValueError('Either an album file path or an album directory must be specified.')

    if album_file_path:
        if not album_file_path.exists():
            raise ValueError('Provided album file path does not exist')

        if not album_file_path.is_file():
            raise ValueError('Provided album file path is not a file')

    if album_dir:
        if not album_dir.exists():
            raise ValueError('Provided album directory does not exist')

        if not album_dir.is_dir():
            raise ValueError('Provided album directory is not a directory')

    logger.info(':: creating album')
    res = requests.post(f'{minori_api_url}/api/albums/-/create', json=body, timeout=30)
    if res.status_code != 200:
        raise ValueError('Create album request failed')
    album_id = res.json()['album']['id']
    logger.info(f':: album created, album id {album_id}')

    if album_file_path:
        logger.info(':: uploading zip to minori')
        with album_file_path.open('rb') as fd:
            res = requests.post(f'{minori_api_url}/api/albums/{album_id}/images/-/bulkcreate', files={'file': fd}, timeout=300)
            if res.status_code != 200:
                raise ValueError('Bulk image upload request failed')
    if album_dir:
        logger.info(':: building zip file from local directory')
        with tempfile.NamedTemporaryFile('rb+') as fd:
            archive = zipfile.ZipFile(fd, mode='w')

            files = natsorted(album_dir.iterdir(), key=lambda file: file.name)
            idx = 0
            for file in files:
                archive.write(file, f'{idx:04}{file.suffix}')
                idx+=1
            archive.close()
            fd.seek(0)
            logger.info(f':: zip file built with {len(files)} files')

            logger.info(':: uploading zip to minori')
            res = requests.post(f'{minori_api_url}/api/albums/{album_id}/images/-/bulkcreate', files={'file': fd}, timeout=300)
            if res.status_code != 200:
                raise ValueError('Bulk image upload request failed')

    logger.info(':: requesting album images')
    res = requests.get(f'{minori_api_url}/api/albums/{album_id}/images', timeout=30)
    if res.status_code != 200:
        raise ValueError('List images request failed')
    cover_image_id = res.json()['images'][0]['id']

    logger.info(':: setting cover to first image')
    res = requests.post(f'{minori_api_url}/api/albums/{album_id}/images/{cover_image_id}/make-cover', timeout=30)
    if res.status_code != 200:
        raise ValueError('Set image as cover image request failed')

    logger.info(':: toggling album visibility')
    res = requests.post(f'{minori_api_url}/api/albums/{album_id}/toggle?state=false', timeout=30)
    if res.status_code != 200:
        raise ValueError('Toggle album visibility request failed')

    logger.info(f'== Successfully created new album ({album_id})')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Creates and uploads a new album to Minori.')
    parser.add_argument(
        '-t',
        '--title',
        type=str,
        help='The title of the album.'
    )
    parser.add_argument(
        '-a',
        '--author',
        type=str,
        help='The author of the album.'
    )
    parser.add_argument(
        '-f',
        '--album-file-path',
        type=Path,
        help='The path to the album archive file.'
    )
    parser.add_argument(
        '-d',
        '--album-dir',
        type=Path,
        help='The path to the album directory.'
    )
    parser.add_argument(
        '-x',
        '--minori-api-url',
        type=str,
        required=True,
        help='The URL of the Minori API.'
    )
    args = parser.parse_args()
    main(**args.__dict__)
