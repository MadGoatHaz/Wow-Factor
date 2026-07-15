"""
Loading overlay screen module.

Provides a reusable loading overlay that dims the background and displays
a centered loading indicator.
"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static
from textual.containers import Container


class LoadingOverlay(Screen):
    """
    A reusable loading overlay widget that dims the background and displays
    a centered loading indicator.
    """

    BINDINGS = [
        ("escape", "dismiss", "Dismiss overlay"),
    ]

    CSS = """
    LoadingOverlay {
        background: rgba(0, 0, 0, 0.4);
    }

    #loading-overlay {
        width: 1fr;
        height: 1fr;
        align: center middle;
    }

    .loading-message {
        text-align: center;
        width: auto;
    }
    """

    def __init__(self, message: str = "Loading...", dim_opacity: float = 0.4) -> None:
        super().__init__()
        self.message = message
        self.dim_opacity = dim_opacity

    def compose(self) -> ComposeResult:
        yield Container(
            Static(
                f"[dim]{self.message}[/dim]",
                classes="loading-message",
                id="loading-text"
            ),
            classes="loading-overlay-container",
            id="loading-overlay",
        )

    def action_dismiss(self) -> None:
        self.dismiss()