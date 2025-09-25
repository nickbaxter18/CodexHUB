import pytest

from src.plugin_manager import discover_plugins, execute_plugins


@pytest.mark.asyncio
async def test_execute_plugins_from_temp_path(tmp_path):
    plugin_file = tmp_path / "example_plugin.py"
    plugin_file.write_text(
        """
from datetime import datetime
from typing import Any, Dict

from src.news_fetcher import NewsArticle


class ExamplePlugin:
    name = "example"

    async def fetch(self, config: Dict[str, Any], *, cache=None, monitor=None):
        return [
            NewsArticle(
                title=config.get("title", "Example"),
                description="Plugin generated",
                url="https://example.com/plugin",
                published_at=None,
                source="plugin",
            )
        ]
"""
    )

    plugins = discover_plugins(paths=[plugin_file])
    assert plugins

    results = await execute_plugins(plugins, {"example": {"title": "Configured"}})
    assert len(results) == 1
    assert results[0].title == "Configured"
