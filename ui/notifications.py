"""
Toast Notification System
Provides a centralized, transient notification widget for consistent user feedback.
"""

from enum import Enum
import time
from typing import Optional, Callable

from ui.theme import ColorPalette


class NotificationType(Enum):
    """Defines the visual style categories for notifications."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ToastNotification:
    """
    A lightweight, overlay widget that displays transient messages.
    Supports auto-dismiss and multiple visual styles.
    
    Attributes:
        message (str): The text content of the notification.
        type (NotificationType): Determines the color scheme/style.
        duration (int): Time in seconds before automatic dismissal.
        on_dismissed (Callable): Optional callback when notification closes.
    """

    # Color definitions for each notification type — sourced from ColorPalette
    _PALETTE = ColorPalette()

    COLORS = {
        NotificationType.SUCCESS: {"bg": _PALETTE.SUCCESS_GREEN, "fg": _PALETTE.TEXT_PRIMARY},
        NotificationType.ERROR: {"bg": _PALETTE.ERROR_RED, "fg": _PALETTE.TEXT_PRIMARY},
        NotificationType.WARNING: {"bg": _PALETTE.WARNING_YELLOW, "fg": _PALETTE.TEXT_DARK},
        NotificationType.INFO: {"bg": _PALETTE.INFO_BLUE, "fg": _PALETTE.TEXT_PRIMARY},
    }

    def __init__(
        self,
        message: str,
        type_: NotificationType = NotificationType.INFO,
        duration: int = 3,
        on_dismissed: Optional[Callable] = None,
    ):
        """
        Initialize the ToastNotification.

        Args:
            message: The notification text to display.
            type_: Visual style category (default: INFO).
            duration: Auto-dismiss time in seconds (default: 3).
            on_dismissed: Callback function triggered when dismissed.
        """
        self.message = message
        self.type = type_
        self.duration = duration
        self.on_dismissed = on_dismissed
        self._dismiss_timer: Optional[float] = None
        self._created_at: float = time.time()

    @property
    def bg_color(self) -> str:
        """Returns the background color for this notification type."""
        return self.COLORS[self.type]["bg"]

    @property
    def fg_color(self) -> str:
        """Returns the foreground (text) color for this notification type."""
        return self.COLORS[self.type]["fg"]

    @property
    def elapsed_time(self) -> float:
        """Returns seconds elapsed since creation."""
        return time.time() - self._created_at

    @property
    def is_expired(self) -> bool:
        """Checks if the notification has exceeded its duration."""
        return self.elapsed_time >= self.duration

    def dismiss(self, immediate: bool = False) -> None:
        """
        Dismiss the notification.

        Args:
            immediate: If True, triggers callback immediately. Otherwise,
                      waits for natural expiration or scheduled timer.
        """
        if self.on_dismissed:
            self.on_dismissed()
        # In Tkinter context, this would call widget.destroy() or hide()

    @classmethod
    def show(cls, parent, message: str, notification_type: NotificationType = NotificationType.INFO, duration: int = 3) -> 'ToastNotification':
        """
        Class method to display a toast notification on the given parent widget.

        Args:
            parent: The parent widget/container where the toast should be displayed.
            message: The notification text to display.
            notification_type: Visual style category (default: INFO).
            duration: Auto-dismiss time in seconds (default: 3).

        Returns:
            The created ToastNotification instance.
        """
        from textual.widgets import Static, Label
        from textual.containers import Container
        from textual.css.query import NoMatches
        
        # Create a container overlay for the toast
        toast_container = Container(id="toast-container")
        toast_container.styles.position = "absolute"
        toast_container.styles.inset = (0, 0, 0, 0)
        toast_container.styles.z = 1000
        
        # Create the toast widget
        toast_label = Label(message, id="toast-label")
        toast_label.styles.background = cls.COLORS[notification_type]["bg"]
        toast_label.styles.color = cls.COLORS[notification_type]["fg"]
        toast_label.styles.padding = (1, 2)
        toast_label.styles.border = "round cyan"
        
        # Add to parent
        parent.mount(toast_container)
        toast_container.mount(toast_label)
        
        # Create notification instance for tracking
        notification = cls(message, notification_type, duration)
        
        # Schedule auto-dismiss using parent's after method (Textual/Tkinter compatible)
        def dismiss_callback():
            try:
                toast_container.remove(toast_label)
                parent.remove(toast_container)
            except NoMatches:
                pass
            if notification.on_dismissed:
                notification.on_dismissed()
        
        # Use parent's scheduling mechanism (Textual uses .after())
        if hasattr(parent, 'after'):
            parent.after(duration * 1000, dismiss_callback)
        elif hasattr(parent, 'schedule'):
            parent.schedule(duration, dismiss_callback)
        
        return notification

    def schedule_auto_dismiss(self, scheduler: Callable[[float], None]) -> None:
        """
        Schedule automatic dismissal using a provided scheduler.

        Args:
            scheduler: A function that accepts delay (seconds) and schedules
                      a callback. Example: root.after(delay_ms, callback)
        """
        remaining = self.duration - self.elapsed_time
        if remaining > 0:
            # Convert to milliseconds for Tkinter compatibility
            scheduler(remaining * 1000, lambda: self.dismiss())
