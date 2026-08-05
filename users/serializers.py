from marshmallow import Schema, fields, validate, EXCLUDE, ValidationError
from PIL import Image, UnidentifiedImageError
import os


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
    updated_at = fields.Str(dump_only=True, allow_none=True)


def validate_avatar_file(uploaded_file):
    if uploaded_file is None:
        return None

    filename = getattr(uploaded_file, 'filename', '') or ''
    if not filename:
        return None

    uploaded_file.seek(0, os.SEEK_END)
    if uploaded_file.tell() == 0:
        uploaded_file.seek(0)
        return None
    uploaded_file.seek(0)

    content_type = getattr(uploaded_file, 'content_type', '') or ''
    if content_type and content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError({
            'avatar_file': [
                'Upload a valid image. The file you uploaded was either not an image or a corrupted image.'
            ]
        })

    try:
        uploaded_file.seek(0)
        image = Image.open(uploaded_file.stream)
        image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise ValidationError({
            'avatar_file': [
                'Upload a valid image. The file you uploaded was either not an image or a corrupted image.'
            ]
        }) from exc
    finally:
        uploaded_file.seek(0)

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
