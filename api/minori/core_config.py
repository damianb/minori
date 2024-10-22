''' just some core configuration bits '''

import os
from pathlib import Path

MINORI_VERSION = '1.2.0'
IMAGE_BASE_FQDN = os.environ.get('IMAGE_BASE_FQDN', '')
FRONTEND_BASE_FQDN = os.environ.get('FRONTEND_BASE_FQDN', '')
CORS_DOMAINS_ALLOWED = os.environ.get('CORS_DOMAIN_ALLOW', '*').split(',')
IMAGE_UPLOAD_PATH=Path(os.environ.get('IMAGE_UPLOAD_PATH', '/srv/images'))
IMAGE_THUMBNAIL_PATH=Path(os.environ.get('IMAGE_THUMBNAIL_PATH', '/srv/thumbs'))
IMAGE_THUMBNAIL_SIZE=int(os.environ.get('IMAGE_THUMBNAIL_SIZE', 500))
ALLOWED_FILE_TYPES = (
    'png',
    'jpg',
    'jpeg',
    'gif',
    'webp',
)
TEMP_PATH = Path('/tmp')
