"""Authentication middleware providing simple header validation."""

from __future__ import annotations

from fastapi import Request, Response


async def authentication_middleware(request: Request, call_next):
    request.state.user = request.headers.get("x-rentalos-user", "anonymous")
    response: Response = await call_next(request)
    response.headers["x-rentalos-user"] = request.state.user
    return response
