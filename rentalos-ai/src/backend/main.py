"""FastAPI application entrypoint."""

from fastapi import FastAPI

from .config import settings
from .controllers import (
    alert_router,
    assets_router,
    community_router,
    energy_router,
    esg_router,
    health_router,
    lease_router,
    maintenance_router,
    payments_router,
    plugin_router,
    pricing_router,
    scheduling_router,
    screening_router,
)
from .middlewares import (
    authentication_middleware,
    compression_middleware,
    logging_middleware,
    register_error_handlers,
)


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.middleware("http")(logging_middleware)
    app.middleware("http")(authentication_middleware)
    app.middleware("http")(compression_middleware)
    register_error_handlers(app)

    app.include_router(assets_router, prefix="/api")
    app.include_router(pricing_router, prefix="/api")
    app.include_router(maintenance_router, prefix="/api")
    app.include_router(lease_router, prefix="/api")
    app.include_router(screening_router, prefix="/api")
    app.include_router(payments_router, prefix="/api")
    app.include_router(esg_router, prefix="/api")
    app.include_router(community_router, prefix="/api")
    app.include_router(scheduling_router, prefix="/api")
    app.include_router(alert_router, prefix="/api")
    app.include_router(energy_router, prefix="/api")
    app.include_router(plugin_router, prefix="/api")
    app.include_router(health_router)
    return app


app = create_app()
