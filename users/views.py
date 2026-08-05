from flask import Blueprint, jsonify, request, Response
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from config.database import db
from config.metrics import USERS_CREATED_TOTAL
from . import store
from .avatars import load_avatar_payload, save_avatar
from .serializers import UserSchema, load_user_payload

api_bp = Blueprint('users_api', __name__)


def _request_data():
    if request.files or request.form:
        data = request.form.to_dict()
        files = request.files
        return data, files
    return request.get_json(silent=True) or {}, None


def _validated_user_data(payload, user_id=None, previous_key=None):
    data = dict(payload)
    uploaded = data.pop('avatar_file', None)

    if uploaded is not None:
        if user_id is None:
            data['_pending_upload'] = uploaded
        else:
            saved = save_avatar(uploaded, user_id, previous_key=previous_key)
            data['avatar'] = saved['avatar']
            data['avatar_key'] = saved['avatar_key']
    return data


def _public_payload(user):
    payload = {
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'avatar': user.get('avatar'),
    }
    if user.get('updated_at'):
        payload['updated_at'] = user['updated_at']
    return payload


def _validation_error_response(exc):
    messages = exc.messages
    if isinstance(messages, dict):
        return jsonify(messages), 400
    return jsonify({'detail': messages}), 400


@api_bp.get('/')
def list_create_users():
    users = [_public_payload(user) for user in store.list_users()]
    return jsonify(UserSchema(many=True).dump(users))


@api_bp.post('/')
def create_user():
    try:
        raw, files = _request_data()
        payload = load_user_payload(raw, files=files, partial=False)
        user = store.create_user(_validated_user_data(payload))
    except ValidationError as exc:
        return _validation_error_response(exc)
    except IntegrityError:
        db.session.rollback()
        return jsonify({'email': ['user with this email already exists.']}), 400

    USERS_CREATED_TOTAL.inc()
    return jsonify(UserSchema().dump(_public_payload(user))), 201


@api_bp.get('/<int:user_id>/')
def get_user(user_id):
    user = store.get_user(user_id)
    if user is None:
        return jsonify({'detail': 'Not found.'}), 404
    return jsonify(UserSchema().dump(_public_payload(user)))


@api_bp.put('/<int:user_id>/')
def put_user(user_id):
    existing = store.get_user(user_id, include_private=True)
    if existing is None:
        return jsonify({'detail': 'Not found.'}), 404

    try:
        raw, files = _request_data()
        payload = load_user_payload(raw, files=files, partial=False)
        user = store.update_user(
            user_id,
            _validated_user_data(
                payload,
                user_id=user_id,
                previous_key=existing.get('avatar_key'),
            ),
        )
    except ValidationError as exc:
        return _validation_error_response(exc)
    except IntegrityError:
        db.session.rollback()
        return jsonify({'email': ['user with this email already exists.']}), 400

    return jsonify(UserSchema().dump(_public_payload(user)))


@api_bp.patch('/<int:user_id>/')
def patch_user(user_id):
    existing = store.get_user(user_id, include_private=True)
    if existing is None:
        return jsonify({'detail': 'Not found.'}), 404

    try:
        raw, files = _request_data()
        payload = load_user_payload(raw, files=files, partial=True)
        user = store.update_user(
            user_id,
            _validated_user_data(
                payload,
                user_id=user_id,
                previous_key=existing.get('avatar_key'),
            ),
            partial=True,
        )
    except ValidationError as exc:
        return _validation_error_response(exc)
    except IntegrityError:
        db.session.rollback()
        return jsonify({'email': ['user with this email already exists.']}), 400

    return jsonify(UserSchema().dump(_public_payload(user)))


@api_bp.delete('/<int:user_id>/')
def delete_user(user_id):
    if not store.delete_user(user_id):
        return jsonify({'detail': 'Not found.'}), 404
    return '', 204


@api_bp.get('/<int:user_id>/avatar/')
def user_avatar(user_id):
    user = store.get_user(user_id, include_private=True)
    if user is None:
        return jsonify({'detail': 'Not found.'}), 404

    payload = load_avatar_payload(user)
    if payload is None:
        return jsonify({'detail': 'Not found.'}), 404

    response = Response(payload['body'], mimetype=payload['content_type'])
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    if payload.get('content_length') is not None:
        response.headers['Content-Length'] = str(payload['content_length'])
    return response
