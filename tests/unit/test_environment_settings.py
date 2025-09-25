import asyncio
from pathlib import Path

import pytest

from src.common.config_loader import ConfigValidationError, load_environment


@pytest.mark.parametrize(
    "content",
    [
        "NODE_ENV=test\nCURSOR_AUTO_INVOCATION_ENABLED=false\n",
        "# comment\n\nNODE_ENV=production\nCURSOR_AUTO_INVOCATION_ENABLED=true\n",
    ],
)
def test_load_environment_accepts_minimal_profiles(tmp_path: Path, content: str) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(content, encoding="utf-8")

    settings = load_environment(env_file)

    assert settings.node_env in {"test", "production"}
    assert settings.cursor_auto_invocation_enabled in {True, False}
    # Defaults should hydrate missing values so CI profiles validate.
    assert settings.session_secret
    assert settings.pipeline_config_path.name == "default.yaml"


@pytest.mark.asyncio()
async def test_load_environment_rejects_invalid_boolean(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("KNOWLEDGE_AUTO_LOAD=not-a-bool\n", encoding="utf-8")

    with pytest.raises(ConfigValidationError):
        load_environment(env_file)

    await asyncio.sleep(0)
