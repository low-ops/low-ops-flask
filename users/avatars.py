import logging
import mimetypes
import os
import uuid

import settings
from storage import s3 as s3_storage

logger = logging.getLogger('lowops.avatars')


def _extension(uploaded_file):
    _, ext = os.path.splitext(getattr(uploaded_file, 'filename', None) or '')
    ext = ext.lower() if ext else ''
    if ext in {'.jpg', '.jpeg', '.png', '.gif', '.webp'}:
        return ext

    content_type = getattr(uploaded_file, 'content_type', '') or ''
    guessed = mimetypes.guess_extension(content_type) or '.jpg'
    if guessed == '.jpe':
        guessed = '.jpg'
    return guessed if guessed in {'.jpg', '.jpeg', '.png', '.gif', '.webp'} else '.jpg'


def _read_bytes(uploaded_file):
    uploaded_file.stream.seek(0)
    return uploaded_file.read()


def save_avatar(uploaded_file, user_id, previous_key=None):
    ext = _extension(uploaded_file)
    content_type = getattr(uploaded_file, 'content_type', None) or mimetypes.guess_type(
        f'file{ext}'
    )[0] or 'application/octet-stream'
    body = _read_bytes(uploaded_file)

    if s3_storage.is_s3_available():
        relative_key = f'avatars/{user_id}/{uuid.uuid4().hex}{ext}'
        key = s3_storage.build_object_key(relative_key)
        try:
            s3_storage.upload_bytes(key, body, content_type)
            if previous_key and previous_key != key:
                s3_storage.delete_object(previous_key)
            return {
                'avatar': f'/api/users/{user_id}/avatar/',
                'avatar_key': key,
            }
        except Exception as exc:
            logger.warning(
                'S3 upload failed for user %s. Falling back to local storage. Reason: %s',
                user_id,
                exc,
            )

    avatars_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
    os.makedirs(avatars_dir, exist_ok=True)
    filename = f'{uuid.uuid4().hex}{ext}'
    path = os.path.join(avatars_dir, filename)
    with open(path, 'wb') as destination:
        destination.write(body)

    return {
        'avatar': f'{settings.MEDIA_URL}avatars/{filename}',
        'avatar_key': None,
    }


def load_avatar_payload(user):
    avatar_key = user.get('avatar_key') if isinstance(user, dict) else user.avatar_key
    avatar = user.get('avatar') if isinstance(user, dict) else user.avatar

    if avatar_key and s3_storage.is_s3_available():
        try:
            return s3_storage.get_object(avatar_key)
        except Exception as exc:
            logger.warning('Failed to load S3 avatar "%s": %s', avatar_key, exc)

    if avatar and str(avatar).startswith('/media/'):
        relative = str(avatar)[len('/media/'):].lstrip('/')
        path = os.path.join(settings.MEDIA_ROOT, relative)
        if os.path.isfile(path):
            content_type = mimetypes.guess_type(path)[0] or 'application/octet-stream'
            with open(path, 'rb') as handle:
                body = handle.read()
            return {
                'body': body,
                'content_type': content_type,
                'content_length': len(body),
            }

    if avatar and str(avatar).startswith('data:'):
        import base64
        import re

        match = re.match(r'^data:([^;]+);base64,(.+)$', str(avatar), re.DOTALL)
        if match:
            body = base64.b64decode(match.group(2))
            return {
                'body': body,
                'content_type': match.group(1),
                'content_length': len(body),
            }

    return None


def delete_avatar(avatar_key):
    if avatar_key:
        s3_storage.delete_object(avatar_key)
