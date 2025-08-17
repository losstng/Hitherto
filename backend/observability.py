"""Observability helpers providing metrics and logging decorators.

This module exposes Prometheus metrics for module execution latency,
counts of successes and failures, as well as gauges for system resource
usage. A decorator ``track`` can be applied to any function or method to
record these metrics and log execution time.
"""
from __future__ import annotations

import logging
import time
from functools import wraps

import psutil
from prometheus_client import Counter, Gauge, Histogram

# ---------------------------------------------------------------------------
# Metrics definitions
# ---------------------------------------------------------------------------
module_latency = Histogram(
    "module_latency_seconds",
    "Time spent executing a module",
    ["module"],
)
module_success = Counter(
    "module_success_total",
    "Number of successful module executions",
    ["module"],
)
module_failure = Counter(
    "module_failure_total",
    "Number of failed module executions",
    ["module"],
)
cycle_latency = Histogram(
    "cycle_latency_seconds",
    "Latency of overseer cycles",
)
cycle_success = Counter(
    "cycle_success_total",
    "Successful overseer cycles",
)
cycle_failure = Counter(
    "cycle_failure_total",
    "Failed overseer cycles",
)

cpu_usage = Gauge("process_cpu_percent", "Process CPU percent")
mem_usage = Gauge("process_memory_mb", "Process memory usage in MB")

logger = logging.getLogger("observability")


def update_system_metrics() -> None:
    """Update gauges for current CPU and memory usage."""
    try:
        cpu_usage.set(psutil.cpu_percent(interval=None))
        mem_usage.set(psutil.Process().memory_info().rss / (1024 * 1024))
    except Exception:  # pragma: no cover - defensive
        pass


def track(module_name: str):
    """Decorator to time a function and record success/failure metrics."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                module_success.labels(module=module_name).inc()
                return result
            except Exception:
                module_failure.labels(module=module_name).inc()
                raise
            finally:
                duration = time.perf_counter() - start
                module_latency.labels(module=module_name).observe(duration)
                logger.debug("%s took %.4fs", module_name, duration)
                update_system_metrics()

        return wrapper

    return decorator


__all__ = [
    "track",
    "module_latency",
    "module_success",
    "module_failure",
    "cycle_latency",
    "cycle_success",
    "cycle_failure",
    "update_system_metrics",
]
