from app import create_app

application = create_app()

with application.app_context():
    from config.backends import ensure_backends

    ensure_backends()
