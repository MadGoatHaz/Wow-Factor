"""Cleanup screens for managing invalid scores and related operations."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static, Button

from ui.shared import WowFactorHeader
from .base_screen import BaseScreen


class ClearInvalidScoresResultScreen(BaseScreen):
    """Screen showing results of clearing invalid scores."""

    BINDINGS = [
        ("b", "go_back", "Back to Main Menu"),
        ("q", "quit_app", "Quit"),
    ]

    def __init__(self, deleted_count: int) -> None:
        super().__init__()
        self.deleted_count = deleted_count
    
    def compose(self) -> ComposeResult:
        with Container(classes="main-menu-container"):
            yield WowFactorHeader(id="app-header")
            if self.deleted_count > 0:
                yield Static(f"Successfully deleted {self.deleted_count} invalid score files.", classes="status-display")
            else:
                yield Static("No invalid score files found to delete.", classes="status-display")
            with Horizontal(classes="action-buttons"):
                yield Button("Back", id="back_to_main_menu", variant="default", classes="action-btn")
    
    def on_mount(self) -> None:
        self.query_one("#app-header", WowFactorHeader).update_title("DELETE COMPLETE")
    
    def action_go_back(self) -> None:
        """Go back to main menu."""
        self.navigation.go_back()
    
    def action_quit_app(self) -> None:
        """Handle quit action."""
        self.app.exit()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back_to_main_menu":
            self.action_go_back()
            event.stop()
        elif event.button.id == "quit_app":
            self.action_quit_app()
            event.stop()
