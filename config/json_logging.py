import json
import logging
from datetime import datetime, timezone


def _trace_context():
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        ctx = span.get_span_context()
        if not ctx or not ctx.is_valid:
            return {}
        return {
            'trace_id': format(ctx.trace_id, '032x'),
            'span_id': format(ctx.span_id, '016x'),
        }
    except Exception:
        return {}


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'level': record.levelname.lower(),
            'message': record.getMessage(),
        }
        payload.update(_trace_context())

        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)
