import logging

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from config.s3_config import MENIX_S3_SERVICE, resolve_s3_config

logger = logging.getLogger('lowops.s3')

_available = False
_client = None
_config = None


def is_s3_available():
    from config.backends import ensure_backends

    ensure_backends()
    return _available


def get_s3_config():
    from config.backends import ensure_backends

    ensure_backends()
    return _config


def init_s3():
    global _available, _client, _config

    config = resolve_s3_config()
    if not config:
        import os

        service_name = (os.environ.get('S3_SERVICE_NAME') or '').strip()
        if (
            service_name.startswith('com.mendix.storage.')
            and service_name != MENIX_S3_SERVICE
        ):
            logger.warning(
                'Storage service "%s" is not S3. Image uploads will use local storage.',
                service_name,
            )
        else:
            logger.warning(
                'S3 is not configured (S3_* env vars missing). '
                'Image uploads will use local storage.'
            )
        _available = False
        _client = None
        _config = None
        return False

    if not config['bucket']:
        logger.warning(
            'S3_BUCKET_NAME is empty after parsing. Image uploads will use local storage.'
        )
        _available = False
        _client = None
        _config = None
        return False

    service_name = config['service_name']
    if service_name.startswith('com.mendix.storage.'):
        service_name = 's3'

    # S3-compatible gateways often reject boto3's newer default checksum behavior.
    client = boto3.client(
        service_name,
        region_name=config['region'],
        endpoint_url=config['endpoint'],
        aws_access_key_id=config['access_key_id'],
        aws_secret_access_key=config['secret_access_key'],
        config=Config(
            s3={'addressing_style': 'path' if config['force_path_style'] else 'auto'},
            request_checksum_calculation='when_required',
            response_checksum_validation='when_required',
        ),
    )

    try:
        _verify_connection(client, config)
        _client = client
        _config = config
        _available = True
        location = (
            f"{config['bucket']}/{config['prefix']}"
            if config['prefix']
            else config['bucket']
        )
        logger.info(
            'S3 connection established (bucket: %s, region: %s)',
            location,
            config['region'],
        )
        return True
    except (BotoCoreError, ClientError, Exception) as exc:
        _available = False
        _client = None
        _config = None
        logger.warning(
            'S3 connection failed. Image uploads will use local storage. Reason: %s',
            exc,
        )
        return False


def _verify_connection(client, config):
    try:
        client.head_bucket(Bucket=config['bucket'])
        return
    except (BotoCoreError, ClientError) as head_error:
        kwargs = {
            'Bucket': config['bucket'],
            'MaxKeys': 1,
        }
        if config['prefix']:
            kwargs['Prefix'] = f"{config['prefix']}/"
        client.list_objects_v2(**kwargs)
        logger.debug(
            'HeadBucket failed but ListObjects succeeded (%s)',
            head_error,
        )


def build_object_key(relative_key):
    if not _config:
        raise RuntimeError('S3 is not available')
    relative_key = relative_key.lstrip('/')
    if _config['prefix']:
        return f"{_config['prefix']}/{relative_key}"
    return relative_key


def upload_bytes(key, body, content_type):
    if not _available or not _client or not _config:
        raise RuntimeError('S3 is not available')

    if isinstance(body, memoryview):
        body = body.tobytes()
    elif not isinstance(body, (bytes, bytearray)):
        body = bytes(body)

    _client.put_object(
        Bucket=_config['bucket'],
        Key=key,
        Body=body,
        ContentType=content_type,
        ContentLength=len(body),
    )
    return key


def get_object(key):
    if not _available or not _client or not _config:
        raise RuntimeError('S3 is not available')
    result = _client.get_object(Bucket=_config['bucket'], Key=key)
    body = result['Body'].read()
    return {
        'body': body,
        'content_type': result.get('ContentType') or 'application/octet-stream',
        'content_length': result.get('ContentLength', len(body)),
    }


def delete_object(key):
    if not key or not _available or not _client or not _config:
        return
    if not _config['perform_delete']:
        return
    try:
        _client.delete_object(Bucket=_config['bucket'], Key=key)
    except (BotoCoreError, ClientError, Exception) as exc:
        logger.warning('Failed to delete S3 object "%s": %s', key, exc)
