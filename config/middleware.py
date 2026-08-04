from flask import request


def apply_no_cache(app):
    @app.after_request
    def _no_cache(response):
        if response.headers.get('Cache-Control'):
            return response

        path = request.path or ''
        if path.startswith('/static/') or path.startswith('/media/'):
            return response

        content_type = response.content_type or ''
        if 'text/html' in content_type or 'application/json' in content_type:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
            response.headers['Pragma'] = 'no-cache'

        return response
