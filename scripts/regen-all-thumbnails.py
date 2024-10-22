#!/usr/bin/env python3
''' regen all minori thumbnails '''
# pylint: disable=invalid-name

import argparse
import logging
import sys

import requests

# set up logging configuration - only to stdout/stderr for now
class ErrorLogFilter(logging.Filter):
    ''' prevents error logs from making it into stdout '''
    def __init__(self, name: str = 'ErrorLogFilter') -> None:
        super().__init__(name)

    def filter(self, record):
        return record.levelno < logging.WARNING

logger = logging.getLogger('script')
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

def main(
        minori_api_url: str
    ) -> None:
    ''' main method '''

    res = requests.get(f'{minori_api_url}/api/albums?include_disabled=true', timeout=30)
    if res.status_code != 200:
        raise ValueError('List albums request failed')

    album_ids = [album['id'] for album in res.json()['albums']]

    logger.info(f'Got {len(album_ids)} album IDs')
    for album_id in album_ids:
        logger.info(f'Regenerating thumbnails for album {album_id}')
        res = requests.post(f'{minori_api_url}/api/albums/{album_id}/images/-/regen-all-thumbnails', timeout=300)
        if res.status_code != 200:
            raise ValueError(f'Regenerate album image thumbnails request failed for album_id "{album_id}"')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Regenerates all thumbnails for minori albums.')
    parser.add_argument(
        '-x',
        '--minori-api-url',
        type=str,
        required=True,
        help='The URL of the Minori API.'
    )
    args = parser.parse_args()
    main(**args.__dict__)
