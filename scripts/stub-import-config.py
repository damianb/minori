#!/usr/bin/env python3
''' stub out the import config '''
# pylint: disable=invalid-name

import argparse
import json
import logging
from pathlib import Path
import sys

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
        config: Path,
        import_dir: Path,
    ) -> None:
    ''' main method '''

    if config.exists():
        raise ValueError('Provided config file path already exists')

    if not import_dir.exists():
        raise ValueError('Provided import directory does not exist')

    if not import_dir.is_dir():
        raise ValueError('Provided import directory is not a directory')

    entries = []
    for directory in import_dir.iterdir():
        if not directory.is_dir():
            continue

        entries.append(directory.as_posix())

    with config.open('a') as fd:
        json.dump([ { 'path': entry, 'author': '', 'title': '', 'enabled': True } for entry in entries ], fd, indent=4)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generates a stub import config from an import directory.')
    parser.add_argument(
        '-c',
        '--config',
        type=Path,
        required=True,
        help='The path to the config file.'
    )
    parser.add_argument(
        '-d',
        '--import-dir',
        type=Path,
        required=True,
        help='The path to the import directory.'
    )
    args = parser.parse_args()
    main(**args.__dict__)
