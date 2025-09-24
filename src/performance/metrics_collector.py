"""
Performance Metrics Collection System
Tracks build times, test coverage, agent response times, and system performance.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, cast


@dataclass
class PerformanceMetric:
    """Individual performance metric with metadata."""

    name: str
    value: float
    unit: str
    timestamp: float
    category: str
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "category": self.category,
            "metadata": self.metadata or {},
        }


@dataclass
class BuildMetrics:
    """Build performance metrics."""

    build_time_seconds: float
    test_time_seconds: float
    lint_time_seconds: float
    total_time_seconds: float
    cache_hit_rate: float
    parallel_tasks: int
    success: bool
    error_message: Optional[str] = None


@dataclass
class AgentMetrics:
    """Agent performance metrics."""

    agent_name: str
    response_time_seconds: float
    task_success: bool
    qa_score: float
    trust_score: float
    error_count: int


class PerformanceCollector:
    """Thread-safe performance metrics collector."""

    def __init__(self, output_dir: Path = Path("results/performance")):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._metrics: List[PerformanceMetric] = []
        self._build_history: List[BuildMetrics] = []
        self._agent_history: List[AgentMetrics] = []

        # Setup logging
        self.logger = logger

    def record_metric(
        self,
        name: str,
        value: float,
        unit: str = "seconds",
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a performance metric."""

        with self._lock:
            metric = PerformanceMetric(
                name=name,
                value=value,
                unit=unit,
                timestamp=time.time(),
                category=category,
                metadata=metadata or {},
            )
            self._metrics.append(metric)
            self.logger.info(f"Recorded metric: {name}={value} {unit}")

    def record_build_metrics(self, metrics: BuildMetrics) -> None:
        """Record build performance metrics."""

        metric_queue: List[Tuple[str, float, str, str, Optional[Dict[str, Any]]]] = [
            ("build_time", float(metrics.build_time_seconds), "seconds", "build", None),
            ("test_time", float(metrics.test_time_seconds), "seconds", "build", None),
            ("lint_time", float(metrics.lint_time_seconds), "seconds", "build", None),
            ("cache_hit_rate", float(metrics.cache_hit_rate), "percent", "build", None),
            ("parallel_tasks", float(metrics.parallel_tasks), "count", "build", None),
        ]

        failure_metadata: Optional[Dict[str, Any]] = None
        if not metrics.success:
            failure_metadata = {"error": metrics.error_message} if metrics.error_message else {}
            metric_queue.append(("build_failure", 1.0, "count", "build", failure_metadata))

        with self._lock:
            self._build_history.append(metrics)

        for name, value, unit, category, metadata in metric_queue:
            self.record_metric(name, value, unit, category, metadata)

    def record_agent_metrics(self, metrics: AgentMetrics) -> None:
        """Record agent performance metrics."""

        metric_queue: List[Tuple[str, float, str, str, Optional[Dict[str, Any]]]] = [
            (
                f"{metrics.agent_name}_response_time",
                float(metrics.response_time_seconds),
                "seconds",
                "agent",
                None,
            ),
            (f"{metrics.agent_name}_qa_score", float(metrics.qa_score), "score", "agent", None),
            (
                f"{metrics.agent_name}_trust_score",
                float(metrics.trust_score),
                "score",
                "agent",
                None,
            ),
        ]

        if not metrics.task_success:
            metric_queue.append(
                (
                    f"{metrics.agent_name}_errors",
                    float(metrics.error_count),
                    "count",
                    "agent",
                    None,
                )
            )

        with self._lock:
            self._agent_history.append(metrics)

        for name, value, unit, category, metadata in metric_queue:
            self.record_metric(name, value, unit, category, metadata)

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""

        with self._lock:
            if not self._metrics:
                return {"message": "No metrics recorded yet"}

            # Calculate summary statistics
            categories: Dict[str, List[float]] = {}
            for metric in self._metrics:
                if metric.category not in categories:
                    categories[metric.category] = []
                categories[metric.category].append(metric.value)

            summary: Dict[str, Any] = {
                "total_metrics": len(self._metrics),
                "categories": {},
                "build_history": len(self._build_history),
                "agent_history": len(self._agent_history),
                "timestamp": datetime.now().isoformat(),
            }

            for category, values in categories.items():
                summary.setdefault("categories", {})[category] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                }

            return summary

    def save_metrics(self, filename: Optional[str] = None) -> Path:
        """Save all metrics to JSON file."""

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_metrics_{timestamp}.json"

        output_path = self.output_dir / filename

        summary = self.get_summary()

        with self._lock:
            data = {
                "summary": summary,
                "metrics": [metric.to_dict() for metric in self._metrics],
                "build_history": [asdict(build) for build in self._build_history],
                "agent_history": [asdict(agent) for agent in self._agent_history],
            }

            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)

            self.logger.info(f"Saved metrics to {output_path}")
            return output_path

    def clear_metrics(self) -> None:
        """Clear all stored metrics."""

        with self._lock:
            self._metrics.clear()
            self._build_history.clear()
            self._agent_history.clear()
            self.logger.info("Cleared all metrics")


# Global collector instance
_global_collector: Optional[PerformanceCollector] = None


def get_performance_collector() -> PerformanceCollector:
    """Get the global performance collector instance."""
    global _global_collector
    if _global_collector is None:
        _global_collector = PerformanceCollector()
    return _global_collector


F = TypeVar("F", bound=Callable[..., Any])


def record_build_time(func: F) -> F:
    """Decorator to record build time for functions."""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result: Any = None
        success = False
        error_msg: Optional[str] = None

        try:
            result = func(*args, **kwargs)
            success = True
            return result
        except Exception as exc:
            error_msg = str(exc)
            raise
        finally:
            end_time = time.time()
            duration = end_time - start_time

            collector = get_performance_collector()
            collector.record_build_metrics(
                BuildMetrics(
                    build_time_seconds=duration,
                    test_time_seconds=0.0,  # Would be measured separately
                    lint_time_seconds=0.0,  # Would be measured separately
                    total_time_seconds=duration,
                    cache_hit_rate=0.0,  # Would be calculated from cache stats
                    parallel_tasks=1,
                    success=success,
                    error_message=error_msg,
                )
            )

    return cast(F, wrapper)


# Export the main classes
__all__ = [
    "PerformanceCollector",
    "PerformanceMetric",
    "BuildMetrics",
    "AgentMetrics",
    "get_performance_collector",
    "record_build_time",
]

logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.addHandler(logging.NullHandler())
