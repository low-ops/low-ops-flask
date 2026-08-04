import logging
import os

from flask import Flask, Response, jsonify, send_from_directory

import settings
from config.database import configure_database_uri, db


def create_app():
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='assets',
        static_url_path='/static',
    )
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['DEBUG'] = settings.DEBUG
    app.config['BASE_DIR'] = settings.BASE_DIR
    app.config['MEDIA_ROOT'] = settings.MEDIA_ROOT
    app.config['MEDIA_URL'] = settings.MEDIA_URL
    app.config['SQLALCHEMY_DATABASE_URI'] = configure_database_uri(settings.BASE_DIR)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

    db.init_app(app)

    _configure_logging(app)
    _configure_cors(app)
    _configure_metrics(app)
    _configure_otel(app)
    _register_blueprints(app)
    _register_ready(app)
    _register_schema(app)
    _register_media_route(app)
    _apply_no_cache(app)

    @app.before_request
    def _ensure_backends():
        from config.backends import ensure_backends

        ensure_backends()

    return app


def _configure_logging(app):
    from config.json_logging import JsonFormatter

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    logging.getLogger('lowops').setLevel(logging.INFO)


def _configure_cors(app):
    from flask_cors import CORS

    if settings.APPLICATION_URL:
        CORS(app, origins=[settings.APPLICATION_URL])
    elif settings.DEBUG:
        CORS(app)


def _configure_metrics(app):
    from config.metrics import apply_metrics

    apply_metrics(app)


def _configure_otel(app):
    from config.otel import setup_otel

    setup_otel(app)


def _register_blueprints(app):
    from users.pages import pages_bp
    from users.views import api_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp, url_prefix='/api/users')


def _register_ready(app):
    @app.get('/ready')
    @app.get('/ready/')
    def ready():
        return Response('ok', status=200, mimetype='text/plain')


def _register_schema(app):
    @app.get('/api/schema')
    def api_schema():
        return jsonify({
            'openapi': '3.0.0',
            'info': {'title': 'Low-Ops Flask API', 'description': 'People desk API', 'version': '1.0.0'},
            'paths': {
                '/api/users/': {
                    'get': {'summary': 'List users', 'tags': ['users']},
                    'post': {'summary': 'Create user', 'tags': ['users']},
                },
                '/api/users/{user_id}/': {
                    'get': {'summary': 'Get user', 'tags': ['users']},
                    'put': {'summary': 'Replace user', 'tags': ['users']},
                    'patch': {'summary': 'Partial update user', 'tags': ['users']},
                    'delete': {'summary': 'Delete user', 'tags': ['users']},
                },
                '/api/users/{user_id}/avatar/': {
                    'get': {'summary': 'Get user avatar', 'tags': ['users']},
                },
                '/ready': {
                    'get': {'summary': 'Health check', 'tags': ['health']},
                },
            },
        })


def _register_media_route(app):
    @app.get('/media/<path:filename>')
    def media_files(filename):
        return send_from_directory(app.config['MEDIA_ROOT'], filename)


def _apply_no_cache(app):
    from config.middleware import apply_no_cache

    apply_no_cache(app)


if __name__ == '__main__':
    application = create_app()
    with application.app_context():
        from config.backends import ensure_backends

        ensure_backends()
    application.run(host='0.0.0.0', port=int(os.environ.get('PORT', '8000')))
