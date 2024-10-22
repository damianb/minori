#!/usr/bin/env python3
''' minori bulk uploader '''
# pylint: disable=invalid-name

import argparse
import json
import logging
from pathlib import Path
import sys
import tempfile
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
        import_config: Path,
        minori_api_url: str,
    ) -> None:
    ''' main method '''

    if not import_config.exists():
        raise ValueError('Provided import config file path does not exist')

    if not import_config.is_file():
        raise ValueError('Provided import config file path is not a file')

    with import_config.open('r') as fd:
        config = json.load(fd)

    for entry in config:
        logger.info(f'Processing entry; path: {json.dumps(entry)}')

        if ('title' not in entry or entry['title'] == '') or ('author' not in entry or entry['author'] == ''):
            logger.error('!! Entry missing required data')
            continue

        album_dir = Path(entry['path'])
        body = {
            'title': entry['title'],
            'author': entry['author']
        }
        enabled = entry['enabled'] if 'enabled' in entry else True

        try:
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

            logger.info(':: building zip file from local directory')
            with tempfile.NamedTemporaryFile('rb+') as fd:
                archive = zipfile.ZipFile(fd, mode='w') # pylint: disable=consider-using-with

                files = natsorted(seq=album_dir.iterdir(), key=lambda file: file.name)
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

            if enabled:
                logger.info(':: toggling album visibility')
                res = requests.post(f'{minori_api_url}/api/albums/{album_id}/toggle?state=false', timeout=30)
                if res.status_code != 200:
                    raise ValueError('Toggle album visibility request failed')

            logger.info(f'== Successfully created new album ({album_id})')
        except Exception as err: # pylint: disable=broad-exception-caught
            logger.error('!! Failed to import album')
            logger.exception(err)
            continue

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Creates and uploads new albums to Minori.')
    parser.add_argument(
        '-c',
        '--import-config',
        type=Path,
        help='The path to the import config file.'
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
