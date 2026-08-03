import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = os.environ.get('SECRET_KEY', 'flask-insecure-your-secret-key-here')
DEBUG = os.environ.get('DEBUG', 'true').lower() in {'1', 'true', 'yes', 'on'}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
