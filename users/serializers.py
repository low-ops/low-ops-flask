from marshmallow import Schema, fields, validate, EXCLUDE, ValidationError
from PIL import Image, UnidentifiedImageError


ALLOWED_IMAGE_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
}


class UserSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    email = fields.Email(required=True)
    avatar = fields.Str(load_default=None, allow_none=True)


def validate_avatar_file(uploaded_file):
    if uploaded_file is None:
        return None

    filename = getattr(uploaded_file, 'filename', '') or ''
    if not filename:
        return None

    content_type = getattr(uploaded_file, 'content_type', '') or ''
    if content_type and content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError({'avatar_file': ['Upload a valid image.']})

    stream = uploaded_file.stream
    pos = stream.tell()
    try:
        image = Image.open(stream)
        image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError({'avatar_file': ['Upload a valid image.']}) from exc
    finally:
        stream.seek(pos)

    return uploaded_file


def load_user_payload(form_or_json, files=None, partial=False):
    schema = UserSchema()
    data = schema.load(form_or_json or {}, partial=partial)

    uploaded = None
    if files is not None:
        uploaded = files.get('avatar_file')
        uploaded = validate_avatar_file(uploaded)

    data.pop('avatar', None)
    if uploaded is not None:
        data['avatar_file'] = uploaded
    return data
