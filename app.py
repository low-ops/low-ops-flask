import logging
import os

from flask import Flask, send_from_directory

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
    _register_blueprints(app)
    _register_media_route(app)

    @app.before_request
    def _ensure_backends():
        from config.backends import ensure_backends

        ensure_backends()

    return app


def _configure_logging(app):
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(name)s: %(message)s',
    )
    logging.getLogger('lowops').setLevel(logging.INFO)


def _register_blueprints(app):
    from users.pages import pages_bp
    from users.views import api_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp, url_prefix='/api/users')


def _register_media_route(app):
    @app.get('/media/<path:filename>')
    def media_files(filename):
        return send_from_directory(app.config['MEDIA_ROOT'], filename)


if __name__ == '__main__':
    application = create_app()
    with application.app_context():
        from config.backends import ensure_backends

        ensure_backends()
    application.run(host='0.0.0.0', port=int(os.environ.get('PORT', '8000')))
