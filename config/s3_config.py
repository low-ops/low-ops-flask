import os
import re
from urllib.parse import urlparse

MENIX_S3_SERVICE = 'com.mendix.storage.s3'
AWS_REGION_PATTERN = re.compile(r'^[a-z]{2}(?:-[a-z]+)+-\d+$')


def parse_boolean_env(value):
    if not value:
        return False
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def parse_bucket_config(raw):
    """Low-Ops sets S3_BUCKET_NAME as `bucket` or `bucket/prefix[/more]`."""
    normalized = raw.strip().strip('/')
    if not normalized:
        return {'bucket': '', 'prefix': ''}

    slash_index = normalized.find('/')
    if slash_index == -1:
        return {'bucket': normalized, 'prefix': ''}

    return {
        'bucket': normalized[:slash_index],
        'prefix': normalized[slash_index + 1:].strip('/'),
    }


def normalize_endpoint(raw):
    trimmed = (raw or '').strip().rstrip('/')
    if not trimmed:
        return trimmed
    if re.match(r'^https?://', trimmed, re.IGNORECASE):
        return trimmed
    return f'https://{trimmed}'


def is_likely_aws_region(value):
    if not value:
        return False
    return bool(AWS_REGION_PATTERN.match(value.strip()))


def extract_region_from_endpoint(endpoint):
    try:
        host = urlparse(normalize_endpoint(endpoint)).hostname or ''
        host = host.lower()
        match = re.search(r'\.s3[.-]([a-z0-9-]+)\.amazonaws\.com$', host) or re.search(
            r'^s3[.-]([a-z0-9-]+)\.amazonaws\.com$', host
        )
        if match and match.group(1) != 'dualstack' and is_likely_aws_region(match.group(1)):
            return match.group(1)
        if host == 's3.amazonaws.com' or host.endswith('.s3.amazonaws.com'):
            return 'us-east-1'
    except Exception:
        return None
    return None


def resolve_s3_region(endpoint):
    for candidate in (
        os.environ.get('S3_REGION'),
        os.environ.get('AWS_REGION'),
        os.environ.get('AWS_DEFAULT_REGION'),
        os.environ.get('S3_SERVICE_NAME'),
    ):
        if is_likely_aws_region(candidate):
            return candidate.strip()
    return extract_region_from_endpoint(endpoint) or 'us-east-1'


def has_s3_config():
    service_name = (os.environ.get('S3_SERVICE_NAME') or '').strip()
    if (
        service_name.startswith('com.mendix.storage.')
        and service_name != MENIX_S3_SERVICE
    ):
        return False

    return bool(
        os.environ.get('S3_ACCESS_KEY_ID')
        and os.environ.get('S3_SECRET_ACCESS_KEY')
        and os.environ.get('S3_BUCKET_NAME')
        and os.environ.get('S3_ENDPOINT')
    )


def resolve_s3_config():
    if not has_s3_config():
        return None

    endpoint = normalize_endpoint(os.environ['S3_ENDPOINT'])
    bucket_parts = parse_bucket_config(os.environ['S3_BUCKET_NAME'])
    region = resolve_s3_region(endpoint)

    return {
        'access_key_id': os.environ['S3_ACCESS_KEY_ID'],
        'secret_access_key': os.environ['S3_SECRET_ACCESS_KEY'],
        'bucket': bucket_parts['bucket'],
        'prefix': bucket_parts['prefix'],
        'endpoint': endpoint,
        'region': region,
        'force_path_style': True,
        'perform_delete': parse_boolean_env(os.environ.get('S3_PERFORM_DELETE')),
        'service_name': (os.environ.get('S3_SERVICE_NAME') or 's3').strip() or 's3',
    }
