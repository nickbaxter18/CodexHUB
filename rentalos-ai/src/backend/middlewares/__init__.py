"""Middleware collection."""

from .auth_middleware import authentication_middleware
from .compression_middleware import compression_middleware
from .error_handler import register_error_handlers
from .logging_middleware import logging_middleware

__all__ = [
    "authentication_middleware",
    "logging_middleware",
    "compression_middleware",
    "register_error_handlers",
]
