import logging
from copy import deepcopy
from itertools import count
from threading import Lock

from config.database import db, is_database_available
from storage import s3 as s3_storage

logger = logging.getLogger('lowops.users')

_id_counter = count(4)
_lock = Lock()

_USERS = {
    1: {
        'id': 1,
        'name': 'Alice Johnson',
        'email': 'alice@example.com',
        'avatar': None,
        'avatar_key': None,
    },
    2: {
        'id': 2,
        'name': 'Bob Smith',
        'email': 'bob@example.com',
        'avatar': None,
        'avatar_key': None,
    },
    3: {
        'id': 3,
        'name': 'Carol Lee',
        'email': 'carol@example.com',
        'avatar': None,
        'avatar_key': None,
    },
}


def log_backend_mode():
    if is_database_available():
        logger.info('Users CRUD is using PostgreSQL')
    else:
        logger.warning('Users CRUD is using in-memory store')

    if s3_storage.is_s3_available():
        logger.info('User images are using S3 storage')
    else:
        logger.warning('User images are using local storage')


def _serialize_db_user(user):
    avatar = user.avatar
    if user.avatar_key:
        avatar = f'/api/users/{user.id}/avatar/'
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'avatar': avatar,
        'avatar_key': user.avatar_key,
    }


def _public_user(user):
    data = {
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'avatar': user.get('avatar'),
    }
    if user.get('avatar_key'):
        data['avatar'] = f"/api/users/{user['id']}/avatar/"
    return data


def list_users():
    if is_database_available():
        from .models import User

        return [_serialize_db_user(user) for user in User.query.order_by(User.id).all()]

    with _lock:
        return [_public_user(user) for user in sorted(_USERS.values(), key=lambda u: u['id'])]


def get_user(user_id, include_private=False):
    if is_database_available():
        from .models import User

        user = db.session.get(User, user_id)
        if user is None:
            return None
        data = _serialize_db_user(user)
        return data if include_private else {
            'id': data['id'],
            'name': data['name'],
            'email': data['email'],
            'avatar': data['avatar'],
        }

    with _lock:
        user = _USERS.get(user_id)
        if user is None:
            return None
        data = deepcopy(user)
        return data if include_private else _public_user(data)


def create_user(data):
    if is_database_available():
        from .models import User

        user = User(
            name=data['name'],
            email=data['email'],
            avatar=data.get('avatar'),
            avatar_key=data.get('avatar_key'),
        )
        db.session.add(user)
        db.session.commit()

        if data.get('_pending_upload') is not None:
            from .avatars import save_avatar

            uploaded = data['_pending_upload']
            saved = save_avatar(uploaded, user.id)
            user.avatar = saved['avatar']
            user.avatar_key = saved['avatar_key']
            db.session.commit()
        return _serialize_db_user(user)

    with _lock:
        user_id = next(_id_counter)
        user = {
            'id': user_id,
            'name': data['name'],
            'email': data['email'],
            'avatar': data.get('avatar'),
            'avatar_key': data.get('avatar_key'),
        }
        if data.get('_pending_upload') is not None:
            from .avatars import save_avatar

            saved = save_avatar(data['_pending_upload'], user_id)
            user['avatar'] = saved['avatar']
            user['avatar_key'] = saved['avatar_key']
        _USERS[user_id] = user
        return _public_user(user)


def update_user(user_id, data, partial=False):
    if is_database_available():
        from .models import User

        user = db.session.get(User, user_id)
        if user is None:
            return None

        if partial:
            for key in ('name', 'email', 'avatar', 'avatar_key'):
                if key in data:
                    setattr(user, key, data[key])
        else:
            user.name = data['name']
            user.email = data['email']
            if 'avatar' in data:
                user.avatar = data.get('avatar')
            if 'avatar_key' in data:
                user.avatar_key = data.get('avatar_key')

        db.session.commit()
        return _serialize_db_user(user)

    with _lock:
        user = _USERS.get(user_id)
        if user is None:
            return None

        if partial:
            for key, value in data.items():
                if key in {'name', 'email', 'avatar', 'avatar_key'}:
                    user[key] = value
        else:
            user['name'] = data['name']
            user['email'] = data['email']
            if 'avatar' in data:
                user['avatar'] = data.get('avatar')
            if 'avatar_key' in data:
                user['avatar_key'] = data.get('avatar_key')

        return _public_user(user)


def delete_user(user_id):
    from .avatars import delete_avatar

    if is_database_available():
        from .models import User

        user = db.session.get(User, user_id)
        if user is None:
            return False
        delete_avatar(user.avatar_key)
        db.session.delete(user)
        db.session.commit()
        return True

    with _lock:
        user = _USERS.pop(user_id, None)
        if user is None:
            return False
        delete_avatar(user.get('avatar_key'))
        return True
