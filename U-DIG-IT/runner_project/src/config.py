"""Application configuration for the runner."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .errors import ConfigurationError


def _default_root() -> Path:
    return Path.cwd()


def _default_knowledge_sources() -> List[Path]:
    """Return default NDJSON knowledge sources if they exist."""

    working_root = _default_root()
    repo_root = Path(__file__).resolve().parents[3]
    search_roots = {working_root, working_root.parent, repo_root}
    candidates: List[Path] = []
    for root in search_roots:
        candidates.extend(
            [
                root / "Brain docs cleansed .ndjson",
                root / "Bundle cleansed .ndjson",
            ]
        )
    return [path for path in candidates if path.exists()]


def _default_plugin_directory() -> Path:
    """Return the default directory where runtime plugins are stored."""

    runner_root = Path(__file__).resolve().parents[2]
    return runner_root / "plugins"


class AppConfig(BaseSettings):
    """Central configuration for the runner."""

    root_dir: Path = Field(default_factory=_default_root)
    allowed_commands: List[str] = Field(
        default_factory=lambda: [
            "ls",
            "pwd",
            "git",
            "pytest",
            "black",
            "python",
            "echo",
        ]
    )
    default_timeout: float = 60.0
    git_timeout: float = 120.0
    task_poll_interval: float = 0.1
    knowledge_sources: List[Path] = Field(default_factory=_default_knowledge_sources)
    simulation_default_steps: int = 5
    simulation_default_runs: int = 100
    fairness_threshold: float = 0.2
    cursor_binary: Optional[str] = Field(default="cursor")
    ui_enabled: bool = True
    plugin_directory: Path = Field(default_factory=_default_plugin_directory)
    health_check_interval: float = 30.0
    max_task_failures: int = 3
    collective_opt_in: bool = True
    fairness_dynamic_margin: float = 0.1

    model_config = SettingsConfigDict(
        env_prefix="RUNNER_",
        arbitrary_types_allowed=True,
    )

    @field_validator("root_dir")
    def validate_root(cls, value: Path) -> Path:
        if not value.exists():
            raise ConfigurationError(f"Root directory does not exist: {value}")
        return value

    @field_validator("allowed_commands")
    def validate_commands(cls, value: List[str]) -> List[str]:
        if not value:
            raise ConfigurationError("At least one allowed command must be configured")
        return value

    @field_validator("knowledge_sources")
    def validate_sources(cls, value: List[Path]) -> List[Path]:
        for path in value:
            if not path.exists():
                raise ConfigurationError(f"Knowledge source does not exist: {path}")
        return value

    @field_validator("plugin_directory")
    def validate_plugin_directory(cls, value: Path) -> Path:
        if value.exists() and not value.is_dir():
            raise ConfigurationError("Plugin directory path must be a directory")
        if not value.exists():
            value.mkdir(parents=True, exist_ok=True)
        return value


@lru_cache()
def get_config() -> AppConfig:
    """Retrieve the cached application configuration."""

    return AppConfig()
