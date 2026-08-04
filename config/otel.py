import logging
import os

logger = logging.getLogger('lowops.otel')


def setup_otel(app):
    endpoint = (os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT') or '').strip()
    if not endpoint:
        return

    service_name = (os.environ.get('OTEL_SERVICE_NAME') or 'low-ops-flask').strip()

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.flask import FlaskInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({'service.name': service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=f'{endpoint.rstrip("/")}/v1/traces')
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        FlaskInstrumentor().instrument_app(app)
        logger.info('OpenTelemetry tracing enabled (service=%s)', service_name)
    except Exception as exc:
        logger.warning('OpenTelemetry setup failed: %s', exc)
