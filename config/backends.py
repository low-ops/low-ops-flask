from threading import RLock

_lock = RLock()
_initialized = False


def ensure_backends():
    """Initialize DB/S3 after the Flask app is fully loaded."""
    global _initialized

    if _initialized:
        return

    with _lock:
        if _initialized:
            return

        from flask import current_app

        from config.database import init_database
        from storage.s3 import init_s3
        from users.store import log_backend_mode

        init_database(current_app._get_current_object())
        init_s3()
        _initialized = True
        log_backend_mode()
