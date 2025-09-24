"""Tokenization service for fractional ownership."""

from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel

from ..utils.logger import get_logger

logger = get_logger(__name__)

_TOKENS: List["TokenizationRecord"] = []


class TokenizationRecord(BaseModel):
    token_id: int
    asset_id: int
    holder: str
    shares: float
    issued_at: datetime


def tokenize_asset(asset_id: int, holder: str, shares: float) -> TokenizationRecord:
    record = TokenizationRecord(
        token_id=len(_TOKENS) + 1,
        asset_id=asset_id,
        holder=holder,
        shares=shares,
        issued_at=datetime.utcnow(),
    )
    _TOKENS.append(record)
    logger.info("Tokenized asset", extra={"asset_id": asset_id, "holder": holder})
    return record


def list_tokens() -> List[TokenizationRecord]:
    return list(_TOKENS)
