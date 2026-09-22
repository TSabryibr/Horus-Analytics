import os
import importlib

def _optional_import(module_name):
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


def _load_sentry_dependencies():
    sentry_sdk = _optional_import("sentry_sdk")
    fastapi_integration = None
    if sentry_sdk is not None:
        integration_module = _optional_import("sentry_sdk.integrations.fastapi")
        if integration_module is not None:
            fastapi_integration = getattr(integration_module, "FastAPIIntegration", None)
    return sentry_sdk, fastapi_integration


def _load_fastapi_instrumentor():
    instrumentor_module = _optional_import("opentelemetry.instrumentation.fastapi")
    if instrumentor_module is None:
        return None
    return getattr(instrumentor_module, "FastAPIInstrumentor", None)


def init_observability(app):
    SENTRY_DSN = os.getenv("SENTRY_DSN", "")
    if SENTRY_DSN:
        sentry_sdk, FastAPIIntegration = _load_sentry_dependencies()
        if sentry_sdk:
            integrations = []
            if FastAPIIntegration:
                integrations.append(FastAPIIntegration())
            sentry_sdk.init(
                dsn=SENTRY_DSN,
                integrations=integrations,
                traces_sample_rate=0.1,
                profiles_sample_rate=0.1,
            )

    FastAPIInstrumentor = _load_fastapi_instrumentor()
    if FastAPIInstrumentor:
        FastAPIInstrumentor.instrument_app(app)
