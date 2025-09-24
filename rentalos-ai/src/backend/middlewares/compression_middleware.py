"""Compression middleware stub."""

from __future__ import annotations

from fastapi import Request, Response


async def compression_middleware(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers.setdefault("Content-Encoding", "identity")
    return response
