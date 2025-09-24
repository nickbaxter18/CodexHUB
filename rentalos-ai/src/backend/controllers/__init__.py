"""Expose routers for FastAPI application."""

from .alert_controller import router as alert_router
from .assets_controller import router as assets_router
from .community_controller import router as community_router
from .energy_controller import router as energy_router
from .esg_controller import router as esg_router
from .health_controller import router as health_router
from .lease_controller import router as lease_router
from .maintenance_controller import router as maintenance_router
from .payments_controller import router as payments_router
from .plugin_controller import router as plugin_router
from .pricing_controller import router as pricing_router
from .scheduling_controller import router as scheduling_router
from .screening_controller import router as screening_router

__all__ = [
    "assets_router",
    "pricing_router",
    "maintenance_router",
    "lease_router",
    "screening_router",
    "payments_router",
    "esg_router",
    "community_router",
    "scheduling_router",
    "alert_router",
    "energy_router",
    "health_router",
    "plugin_router",
]
