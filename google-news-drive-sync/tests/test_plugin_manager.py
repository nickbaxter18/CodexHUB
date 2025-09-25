import pytest

from src.monitor import MonitoringClient
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


@pytest.mark.asyncio
async def test_plugin_timeout_records_error(tmp_path):
    plugin_file = tmp_path / "slow_plugin.py"
    plugin_file.write_text(
        """
import asyncio
from typing import Any, Dict

from src.news_fetcher import NewsArticle


class SlowPlugin:
    name = "slow"

    async def fetch(self, config: Dict[str, Any], *, cache=None, monitor=None):
        await asyncio.sleep(0.2)
        return [
            NewsArticle(
                title="Slow",
                description=None,
                url="https://example.com/slow",
                published_at=None,
                source="slow",
            )
        ]
"""
    )

    plugins = discover_plugins(paths=[plugin_file])
    monitor = MonitoringClient()

    results = await execute_plugins(
        plugins,
        {},
        monitor=monitor,
        sandbox=True,
        timeout=0.05,
    )

    assert results == []
    assert monitor.snapshot().errors == 1
