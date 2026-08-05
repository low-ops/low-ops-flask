import logging
import os

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

logger = logging.getLogger('lowops.database')

db = SQLAlchemy()
_database_available = False


def sqlite_uri(base_dir):
    return f"sqlite:///{os.path.join(base_dir, 'db.sqlite3')}"


def build_postgres_uri():
    user = os.environ.get('POSTGRES_USER')
    password = os.environ.get('POSTGRES_PASSWORD')
    host = os.environ.get('POSTGRES_HOST')
    port = os.environ.get('POSTGRES_PORT') or '5432'
    database = os.environ.get('POSTGRES_DATABASE')

    if not all([user, password, host, database]):
        return None

    return f'postgresql+psycopg://{user}:{password}@{host}:{port}/{database}'


def configure_database_uri(base_dir):
    postgres = build_postgres_uri()
    if postgres:
        return postgres
    return sqlite_uri(base_dir)


def is_database_available():
    from config.backends import ensure_backends

    ensure_backends()
    return _database_available


def init_database(app):
    global _database_available

    postgres = build_postgres_uri()
    if not postgres:
        _database_available = False
        logger.warning(
            'Database is not configured (POSTGRES_* env vars missing). '
            'Falling back to in-memory users store.'
        )
        return False

    try:
        with app.app_context():
            with db.engine.connect() as connection:
                connection.execute(text('SELECT 1'))
        _database_available = True
        logger.info(
            'Database connection established (%s:%s/%s)',
            os.environ.get('POSTGRES_HOST'),
            os.environ.get('POSTGRES_PORT') or '5432',
            os.environ.get('POSTGRES_DATABASE'),
        )
        return True
    except Exception as exc:
        _database_available = False
        logger.warning(
            'Database connection failed. Falling back to in-memory users store. Reason: %s',
            exc,
        )
        return False


def seed_demo_users():
    if not _database_available:
        return

    from users.models import User

    if User.query.first() is not None:
        return

    demo_users = (
        ('Alice Johnson', 'alice@example.com'),
        ('Bob Smith', 'bob@example.com'),
        ('Carol Lee', 'carol@example.com'),
    )
    for name, email in demo_users:
        db.session.add(User(name=name, email=email))
    db.session.commit()
    logger.info('Seeded demo users in PostgreSQL')
