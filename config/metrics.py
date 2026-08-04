import os
import threading
import time

from prometheus_client import Counter, Gauge, Histogram, start_http_server

HTTP_REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'path', 'status'],
)
HTTP_ACTIVE_REQUESTS = Gauge(
    'http_active_requests',
    'Number of in-flight HTTP requests',
)
HTTP_ERRORS_TOTAL = Counter(
    'http_errors_total',
    'Total HTTP error responses',
    ['method', 'path', 'status'],
)
USERS_CREATED_TOTAL = Counter(
    'users_created_total',
    'Total users created',
)

_lock = threading.Lock()
_started = False


def start_metrics_server():
    global _started
    with _lock:
        if _started:
            return
        port = int(os.environ.get('METRICS_PORT', '8001'))
        try:
            start_http_server(port)
            _started = True
        except OSError:
            _started = True


def normalize_path(path):
    parts = path.strip('/').split('/')
    normalized = []
    for part in parts:
        if part.isdigit():
            normalized.append(':id')
        else:
            normalized.append(part)
    return '/' + '/'.join(normalized) if normalized and normalized != [''] else '/'


def apply_metrics(app):
    from flask import g, request

    start_metrics_server()

    @app.before_request
    def _before():
        if request.path in {'/ready', '/ready/'}:
            return
        HTTP_ACTIVE_REQUESTS.inc()
        g._metrics_start = time.perf_counter()
        g._metrics_path = normalize_path(request.path)

    @app.after_request
    def _after(response):
        if request.path in {'/ready', '/ready/'}:
            return response
        started = getattr(g, '_metrics_start', None)
        if started is None:
            return response
        duration = time.perf_counter() - started
        path = getattr(g, '_metrics_path', '/')
        status = str(response.status_code)
        HTTP_ACTIVE_REQUESTS.dec()
        HTTP_REQUEST_DURATION.labels(
            method=request.method,
            path=path,
            status=status,
        ).observe(duration)
        if status.startswith(('4', '5')) and status != '404':
            HTTP_ERRORS_TOTAL.labels(
                method=request.method,
                path=path,
                status=status,
            ).inc()
        return response
