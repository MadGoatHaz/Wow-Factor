#!/usr/bin/env python3
"""
Dependency Injection service registry for WowFactor TUI.

Provides a thread-safe singleton registry that supports lazy initialization
and singleton-scoped service resolution. Designed to break tight coupling
between core modules and enable test mocking.
"""

import threading
from typing import Any, Callable, Dict, Optional


class ServiceRegistryError(Exception):
    """Base exception for service registry operations."""
    pass


class ServiceNotFoundError(ServiceRegistryError):
    """Raised when resolving a service that has not been registered."""
    def __init__(self, name: str):
        super().__init__(f"Service '{name}' is not registered")
        self.name = name


class ServiceAlreadyRegisteredError(ServiceRegistryError):
    """Raised when registering a service that already exists."""
    def __init__(self, name: str):
        super().__init__(f"Service '{name}' is already registered")
        self.name = name


class ServiceRegistry:
    """
    Thread-safe singleton service registry.

    Supports lazy initialization via callable factories and singleton
    semantics (each registered name yields exactly one instance).

    Usage:
        registry = ServiceRegistry()
        registry.register('config', lambda: ConfigManager())
        config = registry.resolve('config')  # lazy factory call, cached

    All public methods are thread-safe via an internal Lock.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # factory(name) -> instance or provider dict
        self._factories: Dict[str, Callable[[], Any]] = {}
        # resolved instances (singletons)
        self._instances: Dict[str, Any] = {}
        # whether each name has been resolved yet
        self._resolved: Dict[str, bool] = {}

    # -- registration --------------------------------------------------------

    def register(self, name: str, factory: Callable[[], Any]) -> None:
        """
        Register a service with a lazy factory callable.

        Args:
            name: Unique service identifier.
            factory: Zero-argument callable returning the service instance.
                     Called on first resolution (lazy singleton).

        Raises:
            ServiceAlreadyRegisteredError: If *name* is already registered.
        """
        if not callable(factory):
            raise TypeError(f"Factory for '{name}' must be callable, got {type(factory).__name__}")

        with self._lock:
            if name in self._factories:
                raise ServiceAlreadyRegisteredError(name)
            self._factories[name] = factory
            # Ensure resolved flag exists (already resolved only if previously cached)
            if name not in self._resolved:
                self._resolved[name] = False

    def is_registered(self, name: str) -> bool:
        """Return True if a factory has been registered for *name*."""
        with self._lock:
            return name in self._factories

    def unregister(self, name: str) -> None:
        """
        Remove a service registration and its cached instance.

        Raises:
            ServiceNotFoundError: If *name* is not registered.
        """
        with self._lock:
            if name not in self._factories:
                raise ServiceNotFoundError(name)
            del self._factories[name]
            self._resolved.pop(name, None)
            self._instances.pop(name, None)

    # -- resolution ----------------------------------------------------------

    def resolve(self, name: str) -> Any:
        """
        Resolve a registered service to its singleton instance.

        The factory is invoked on first call and the result is cached.
        Subsequent calls return the cached instance.

        Args:
            name: Registered service identifier.

        Returns:
            The singleton instance for *name*.

        Raises:
            ServiceNotFoundError: If *name* is not registered.
        """
        with self._lock:
            if name not in self._factories:
                raise ServiceNotFoundError(name)

            if self._resolved[name]:
                return self._instances[name]

            factory = self._factories[name]
            instance = factory()
            self._instances[name] = instance
            self._resolved[name] = True
            return instance

    def resolve_all(self) -> Dict[str, Any]:
        """
        Resolve every registered service and return them as a dict.

        Returns:
            {name: instance, ...} for all registered services.
        """
        with self._lock:
            names = list(self._factories.keys())

        results: Dict[str, Any] = {}
        for name in names:
            results[name] = self.resolve(name)
        return results

    def clear(self) -> None:
        """Remove all registrations and cached instances."""
        with self._lock:
            self._factories.clear()
            self._instances.clear()
            self._resolved.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._factories)

    def __contains__(self, name: str) -> bool:
        return self.is_registered(name)

    def __repr__(self) -> str:  # noqa: D105
        with self._lock:
            count = len(self._factories)
        return f"ServiceRegistry(services={count})"