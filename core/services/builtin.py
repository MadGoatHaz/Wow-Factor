#!/usr/bin/env python3
"""
Builtin service registrations for WowFactor TUI.

Registers the existing core modules as singletons behind the DI registry
so downstream code can resolve them without direct imports.

Each service is registered with a lazy factory (zero-argument callable)
that is invoked on first resolution.
"""

import logging
from typing import TYPE_CHECKING

from core.services.registry import ServiceRegistry

if TYPE_CHECKING:
    from core.config import ConfigManager
    from core.analytics_engine import AnalyticsEngine
    from core.comparator import Comparator
    from core.exporters import Exporter
    from core.power import PowerManager
    from core.benchmark import BenchmarkRunner


logger = logging.getLogger(__name__)


def _register_config(registry: ServiceRegistry) -> None:
    """Register ConfigManager as the 'config' service."""
    # Deferred import to avoid circular dependency at module level.
    from core.config import ConfigManager

    def _factory() -> "ConfigManager":
        return ConfigManager()

    registry.register("config", _factory)


def _register_benchmark(registry: ServiceRegistry) -> None:
    """Register benchmark module-level functions as the 'benchmark' service."""
    # The benchmark module exports several functions; we expose the module
    # itself so callers can invoke any of the exported API surface.
    import core.benchmark as _benchmark_mod

    def _factory() -> object:
        return _benchmark_mod

    registry.register("benchmark", _factory)


def _register_analytics(registry: ServiceRegistry) -> None:
    """Register analytics engine as the 'analytics' service."""
    from core.analytics_engine import AnalyticsEngine

    def _factory() -> "AnalyticsEngine":
        return AnalyticsEngine()

    registry.register("analytics", _factory)


def _register_comparator(registry: ServiceRegistry) -> None:
    """Register comparator functions as the 'comparator' service."""
    import core.comparator as _comparator_mod

    def _factory() -> object:
        return _comparator_mod

    registry.register("comparator", _factory)


def _register_exporter(registry: ServiceRegistry) -> None:
    """Register exporter functions as the 'exporter' service."""
    import core.exporters as _exporter_mod

    def _factory() -> object:
        return _exporter_mod

    registry.register("exporter", _factory)


def _register_power(registry: ServiceRegistry) -> None:
    """Register power management functions as the 'power' service."""
    import core.power as _power_mod

    def _factory() -> object:
        return _power_mod

    registry.register("power", _factory)


def register_builtin_services(registry: ServiceRegistry) -> ServiceRegistry:
    """
    Register all builtin core services onto *registry*.

    This is the entry-point called by application startup code.

    Args:
        registry: A ServiceRegistry instance to populate.

    Returns:
        The same registry instance (for chaining).
    """
    _register_config(registry)
    _register_benchmark(registry)
    _register_analytics(registry)
    _register_comparator(registry)
    _register_exporter(registry)
    _register_power(registry)
    logger.info(
        "Registered builtin services: %s",
        sorted(registry.resolve_all().keys()),
    )
    return registry