#!/usr/bin/env python3
"""
Dependency Injection service registry for WowFactor TUI.

Exports:
    ServiceRegistry  - Thread-safe singleton registry with lazy factories.
    ServiceContainer - Convenience alias (same as ServiceRegistry).
"""

from core.services.registry import (
    ServiceAlreadyRegisteredError,
    ServiceNotFoundError,
    ServiceRegistry,
    ServiceRegistryError,
)

# Convenience alias — the container *is* the registry.
ServiceContainer = ServiceRegistry

__all__ = [
    "ServiceAlreadyRegisteredError",
    "ServiceContainer",
    "ServiceNotFoundError",
    "ServiceRegistry",
    "ServiceRegistryError",
]