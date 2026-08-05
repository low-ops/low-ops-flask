import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def normalize_application_url(raw_url):
    url = (raw_url or '').strip().rstrip('/')
    if not url:
        return ''

    if '://' in url:
        return url

    if url.startswith('localhost') or url.startswith('127.0.0.1'):
        return f'http://{url}'

    return f'https://{url}'


SECRET_KEY = os.environ.get('SECRET_KEY', 'flask-insecure-your-secret-key-here')
DEBUG = os.environ.get('DEBUG', 'true').lower() in {'1', 'true', 'yes', 'on'}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

APPLICATION_URL = normalize_application_url(os.environ.get('APPLICATION_URL'))
