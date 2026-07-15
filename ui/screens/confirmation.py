"""
Confirmation screen module.

Provides confirmation dialogs for destructive actions like clearing invalid scores.
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.widgets import Static, Button, Footer, Footer

from ui.screens.base_screen import BaseScreen
from ui.shared import RETRO_GRADIENT_COLORS, WowFactorHeader, colorize_text_gradient


class ClearInvalidScoresConfirmationScreen(BaseScreen):
    """
    Confirmation screen for clearing invalid benchmark scores.
    Displays the count of invalid files and asks user to confirm deletion.
    """
    def __init__(self, invalid_count: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.invalid_count = invalid_count

    BINDINGS = [
        ("y", "confirm_clear", "Confirm Clear"),
        ("n", "cancel_clear", "Cancel"),
        ("q", "quit_app", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Container():
            yield WowFactorHeader(id="app-header")
            yield Static(
                colorize_text_gradient("CLEAR INVALID SCORES", RETRO_GRADIENT_COLORS),
                classes="title"
            )
            yield Static(f"Found {self.invalid_count} invalid score file(s).", id="info_display")
            yield Static("Are you sure you want to delete them?", id="confirm_message")
            with Horizontal(classes="action-buttons"):
                yield Button("Yes, Clear All", id="confirm_clear", variant="error")
                yield Button("Cancel", id="cancel_clear", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#app-header", WowFactorHeader).update_title("CLEAR INVALID SCORES CONFIRMATION")

    def action_confirm_clear(self) -> None:
        # Post message to parent screen that user confirmed
        self.post_message(ClearInvalidScoresConfirmed(self.invalid_count))
        self.app.pop_screen()

    def action_cancel_clear(self) -> None:
        self.app.pop_screen()


class ClearInvalidScoresConfirmed(Message):
    """
    Message posted when user confirms clearing invalid scores.
    Contains the count of files that will be deleted.
    """
    def __init__(self, file_count: int):
        self.file_count = file_count
        super().__init__()