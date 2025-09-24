"""Plugin marketplace endpoints for Stage 3."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..services import api_service

router = APIRouter(tags=["plugins"])

_last_errors: List[str] = []


class PluginModel(BaseModel):
    name: str
    version: str
    description: str
    enabled: bool
    permissions: List[str]
    webhooks: List[str]
    entrypoint: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    signature: Optional[str] = None
    source: Optional[str] = None


class PluginListResponse(BaseModel):
    plugins: List[PluginModel]
    errors: List[str] = Field(default_factory=list)


class ReloadRequest(BaseModel):
    path: Optional[str] = None
    strict: Optional[bool] = None


def _serialize_plugins() -> List[PluginModel]:
    return [PluginModel.model_validate(payload) for payload in api_service.list_plugins().values()]


def _load_default_registry() -> None:
    if api_service.list_plugins():
        return
    loaded, errors = api_service.reload_default_plugins()
    _last_errors.clear()
    _last_errors.extend(errors)
    if not loaded and errors:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load any plugins",
        )


@router.get("/plugins", response_model=PluginListResponse)
def list_plugins() -> PluginListResponse:
    _load_default_registry()
    return PluginListResponse(plugins=_serialize_plugins(), errors=list(_last_errors))


@router.post(
    "/plugins/reload", response_model=PluginListResponse, status_code=status.HTTP_202_ACCEPTED
)
def reload_plugins(request: ReloadRequest) -> PluginListResponse:
    plugin_path = Path(request.path) if request.path else api_service.DEFAULT_PLUGIN_ROOT
    try:
        loaded, errors = api_service.load_plugins_from_directory(plugin_path, strict=request.strict)
    except FileNotFoundError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    _last_errors.clear()
    _last_errors.extend(errors)
    if not loaded and errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": errors},
        )
    return PluginListResponse(plugins=_serialize_plugins(), errors=list(_last_errors))


@router.post("/plugins/{name}/enable", response_model=PluginModel)
def enable_plugin(name: str) -> PluginModel:
    try:
        plugin = api_service.enable_plugin(name)
    except KeyError as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found"
        ) from exc
    return PluginModel.model_validate(plugin)


@router.post("/plugins/{name}/disable", response_model=PluginModel)
def disable_plugin(name: str) -> PluginModel:
    try:
        plugin = api_service.disable_plugin(name)
    except KeyError as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found"
        ) from exc
    return PluginModel.model_validate(plugin)


@router.get("/plugins/{name}", response_model=PluginModel)
def get_plugin(name: str) -> PluginModel:
    try:
        plugin = api_service.get_plugin(name)
    except KeyError as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found"
        ) from exc
    return PluginModel.model_validate(plugin)
