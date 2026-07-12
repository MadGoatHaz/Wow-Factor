"""Navigation Manager for WowFactor TUI.

Provides centralized screen navigation management to decouple screens from each other.
Implements a singleton pattern for the NavigationManager service.
"""

from typing import TYPE_CHECKING, Optional, Type

if TYPE_CHECKING:
    from ui.app import WowFactorTUI


class NavigationManager:
    """Singleton service that manages screen navigation in the application.
    
    This class provides a centralized way to navigate between screens using
    string-based screen names rather than direct class instantiation, which
    decouples screens from each other and centralizes application flow.
    """
    
    _instance: Optional['NavigationManager'] = None
    _app: Optional['WowFactorTUI'] = None
    
    def __new__(cls) -> 'NavigationManager':
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self, app: 'WowFactorTUI') -> None:
        """Initialize the NavigationManager with a reference to the main app.
        
        Args:
            app: The WowFactorTUI application instance.
        """
        self._app = app
    
    @property
    def app(self) -> 'WowFactorTUI':
        """Get the app reference."""
        if self._app is None:
            raise RuntimeError("NavigationManager not initialized. Call initialize() first.")
        return self._app
    
    def navigate_to(self, screen_name: str, **kwargs) -> None:
        """Navigate to a screen by its registered name.
        
        Args:
            screen_name: The key used in the app's SCREENS registry.
            **kwargs: Optional keyword arguments passed to the screen constructor.
        """
        if screen_name not in self.app.SCREENS:
            raise ValueError(f"Unknown screen name: {screen_name}. Available screens: {list(self.app.SCREENS.keys())}")
        
        screen_class = self.app.SCREENS[screen_name]
        # Instantiate the screen with any provided kwargs
        screen_instance = screen_class(**kwargs)
        self.app.push_screen(screen_instance)
    
    def go_back(self) -> None:
        """Pop the current screen and return to the previous one."""
        if len(self.app.screen_stack) > 1:
            self.app.pop_screen()
    
    def reset_to_main(self) -> None:
        """Reset navigation to the main menu screen.
        
        Pops all screens until only the main_menu remains, then ensures it's displayed.
        """
        # Pop screens until we reach main_menu
        while len(self.app.screen_stack) > 1:
            self.app.pop_screen()
        
        # Ensure main_menu is active
        if self.app.current_screen and hasattr(self.app.current_screen, 'id'):
            if self.app.current_screen.id != "main_menu":
                self.app.push_screen("main_menu")
    
    def notify(self, message: str, type: str = "info") -> None:
        """Display a toast notification to the user.
        
        Args:
            message: The notification message text.
            type: Notification type - one of 'success', 'error', 'warning', or 'info'.
        """
        from ui.notifications import ToastNotification, NotificationType
        
        # Map string type to NotificationType enum
        type_mapping = {
            'success': NotificationType.SUCCESS,
            'error': NotificationType.ERROR,
            'warning': NotificationType.WARNING,
            'info': NotificationType.INFO
        }
        
        notification_type = type_mapping.get(type.lower(), NotificationType.INFO)
        
        # Show the toast notification on the current screen
        if self.app.current_screen:
            ToastNotification.show(
                parent=self.app.current_screen,
                message=message,
                notification_type=notification_type
            )
