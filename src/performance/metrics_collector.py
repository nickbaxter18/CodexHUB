"""
Performance Metrics Collection System
Tracks build times, test coverage, agent response times, and system performance.
"""

from __future__ import annotations

import time
import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from threading import Lock


@dataclass
class PerformanceMetric:
    """Individual performance metric with metadata."""
    
    name: str
    value: float
    unit: str
    timestamp: float
    category: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "category": self.category,
            "metadata": self.metadata or {}
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
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def record_metric(
        self,
        name: str,
        value: float,
        unit: str = "seconds",
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a performance metric."""
        
        with self._lock:
            metric = PerformanceMetric(
                name=name,
                value=value,
                unit=unit,
                timestamp=time.time(),
                category=category,
                metadata=metadata or {}
            )
            self._metrics.append(metric)
            self.logger.info(f"Recorded metric: {name}={value} {unit}")
    
    def record_build_metrics(self, metrics: BuildMetrics) -> None:
        """Record build performance metrics."""
        
        with self._lock:
            self._build_history.append(metrics)
            
            # Record individual metrics
            self.record_metric("build_time", metrics.build_time_seconds, "seconds", "build")
            self.record_metric("test_time", metrics.test_time_seconds, "seconds", "build")
            self.record_metric("lint_time", metrics.lint_time_seconds, "seconds", "build")
            self.record_metric("cache_hit_rate", metrics.cache_hit_rate, "percent", "build")
            self.record_metric("parallel_tasks", metrics.parallel_tasks, "count", "build")
            
            if not metrics.success:
                self.record_metric("build_failure", 1, "count", "build", {"error": metrics.error_message})
    
    def record_agent_metrics(self, metrics: AgentMetrics) -> None:
        """Record agent performance metrics."""
        
        with self._lock:
            self._agent_history.append(metrics)
            
            # Record individual metrics
            self.record_metric(
                f"{metrics.agent_name}_response_time",
                metrics.response_time_seconds,
                "seconds",
                "agent"
            )
            self.record_metric(
                f"{metrics.agent_name}_qa_score",
                metrics.qa_score,
                "score",
                "agent"
            )
            self.record_metric(
                f"{metrics.agent_name}_trust_score",
                metrics.trust_score,
                "score",
                "agent"
            )
            
            if not metrics.task_success:
                self.record_metric(f"{metrics.agent_name}_errors", metrics.error_count, "count", "agent")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        
        with self._lock:
            if not self._metrics:
                return {"message": "No metrics recorded yet"}
            
            # Calculate summary statistics
            categories = {}
            for metric in self._metrics:
                if metric.category not in categories:
                    categories[metric.category] = []
                categories[metric.category].append(metric.value)
            
            summary = {
                "total_metrics": len(self._metrics),
                "categories": {},
                "build_history": len(self._build_history),
                "agent_history": len(self._agent_history),
                "timestamp": datetime.now().isoformat()
            }
            
            for category, values in categories.items():
                summary["categories"][category] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values)
                }
            
            return summary
    
    def save_metrics(self, filename: Optional[str] = None) -> Path:
        """Save all metrics to JSON file."""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_metrics_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        with self._lock:
            data = {
                "summary": self.get_summary(),
                "metrics": [metric.to_dict() for metric in self._metrics],
                "build_history": [asdict(build) for build in self._build_history],
                "agent_history": [asdict(agent) for agent in self._agent_history]
            }
            
            with open(output_path, 'w') as f:
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


def record_build_time(func):
    """Decorator to record build time for functions."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            success = True
            error_msg = None
        except Exception as e:
            success = False
            error_msg = str(e)
            raise
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            collector = get_performance_collector()
            collector.record_build_metrics(BuildMetrics(
                build_time_seconds=duration,
                test_time_seconds=0,  # Would be measured separately
                lint_time_seconds=0,  # Would be measured separately
                total_time_seconds=duration,
                cache_hit_rate=0,  # Would be calculated from cache stats
                parallel_tasks=1,
                success=success,
                error_message=error_msg
            ))
        
        return result
    return wrapper


# Export the main classes
__all__ = [
    "PerformanceCollector",
    "PerformanceMetric", 
    "BuildMetrics",
    "AgentMetrics",
    "get_performance_collector",
    "record_build_time"
]
