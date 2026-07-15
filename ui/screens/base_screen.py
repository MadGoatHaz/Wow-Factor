"""
Base screen classes with service injection support.

This module provides:
- ScreenWithServices: Mixin class for Textual screens to access registered services
- BaseScreen: Template class for extracted screens with Footer widget
"""

from typing import Any, Optional
from textual.app import ComposeResult
from textual.screen import Screen as TextualScreen
from textual.widgets import Footer


class ScreenWithServices:
    """
    Mixin for Textual screens to access registered services.
    
    Provides dependency injection capabilities by accessing the global
    service registry (_registry) from the core module.
    Also provides direct access to the NavigationManager singleton.
    """
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._services: Optional[Any] = None
        self._navigation: Optional[Any] = None
    
    @property
    def services(self) -> Any:
        """
        Get the service registry instance.
        
        Lazy-loads the _registry from core module on first access.
        
        Returns:
            The service registry instance.
        """
        if self._services is None:
            from core import _registry
            self._services = _registry
        return self._services
    
    @property
    def navigation(self) -> Any:
        """
        Get the NavigationManager singleton instance.
        
        Lazy-loads the NavigationManager on first access.
        This provides a convenient way for screens to navigate without
        needing to import the manager directly.
        
        Returns:
            The NavigationManager singleton instance.
        """
        if self._navigation is None:
            from ui.navigation import NavigationManager
            self._navigation = NavigationManager()
        return self._navigation
    
    def get_service(self, name: str) -> Optional[Any]:
        """
        Retrieve a registered service by name.
        
        Args:
            name: The name of the service to retrieve.
            
        Returns:
            The service instance if found, None otherwise.
        """
        return self.services.get(name)
    
    def has_service(self, name: str) -> bool:
        """
        Check if a service is registered.
        
        Args:
            name: The name of the service to check.
            
        Returns:
            True if the service is registered, False otherwise.
        """
        return self.services.has(name)


class BaseScreen(ScreenWithServices, TextualScreen):
    """
    Template class for extracted screens with service injection.
    
    This base class combines:
    - ScreenWithServices: For dependency injection via services mixin
    - TextualScreen: The base Textual screen class
    
    Subclasses should override the on_show() method to implement
    their specific UI logic and use get_service()/has_service()
    for accessing dependencies.
    """
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        """
        Compose the base screen widget tree.

        Yields a Footer widget that auto-docks to the bottom and displays
        keybindings from the screen's BINDINGS attribute. Subclasses should
        yield their content first, then include Footer via:
            yield Footer()
        or by calling yield from super().compose() at the end.
        """
        yield Footer()

    def on_show(self) -> None:
        """
        Called when the screen is shown.
        
        Override this method in subclasses to implement
        initialization logic that requires service access.
        """
        pass
