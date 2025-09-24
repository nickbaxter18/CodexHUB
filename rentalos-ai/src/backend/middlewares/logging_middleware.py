"""Request logging middleware."""

from __future__ import annotations

import time
from typing import Callable

from fastapi import Request, Response

from ..utils.logger import get_logger

logger = get_logger(__name__)


async def logging_middleware(request: Request, call_next: Callable):
    start = time.time()
    response: Response = await call_next(request)
    duration = time.time() - start
    logger.info(
        "Handled request",
        extra={
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
        },
    )
    return response
