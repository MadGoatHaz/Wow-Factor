#!/usr/bin/env python3
"""
Shared UI components for WowFactor TUI Application.
This module contains reusable components that don't depend on other UI modules,
avoiding circular import issues.
"""

from textual.app import ComposeResult
from textual.widgets import Static, Button
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.message import Message
from typing import List

# Import theme system for centralized design tokens
from ui.theme import ColorPalette

# --- Gradient and Color Definitions (UI assets) ---
RETRO_GRADIENT_COLORS = [
    ColorPalette.ACCENT_MAGENTA,
    ColorPalette.ACCENT_PINK,
    ColorPalette.PRIMARY_CYAN,
    ColorPalette.PRIMARY_BLUE,
    ColorPalette.SUCCESS_GREEN,
    ColorPalette.ACCENT_YELLOW,
    ColorPalette.ACCENT_ORANGE,
    ColorPalette.ACCENT_YELLOW,
    ColorPalette.ERROR_RED,
    ColorPalette.ACCENT_ORANGE
]


def colorize_text_gradient(text: str, colors: List[str]) -> str:
    """Simple colorize function for Textual's rich content."""
    if not colors:
        return text
    num_colors = len(colors)
    colored_chars = []
    for i, char in enumerate(text):
        if char.isspace():
            colored_chars.append(char)
        else:
            color = colors[i % num_colors]
            colored_chars.append(f"[{color}]{char}[/{color}]")
    return "".join(colored_chars)


class WowFactorHeader(Static):
    """
    Header widget displaying the application title and version.
    Used across multiple screens for consistent branding.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _render_header(self, dynamic_text: str) -> str:
        gradient_text = colorize_text_gradient(dynamic_text, RETRO_GRADIENT_COLORS)
        return f"[bold magenta]WowFactor Benchmark Utility[/]  |  {gradient_text}"

    def update_title(self, new_title: str) -> None:
        self.update(self._render_header(new_title))


class ClearInvalidScoresConfirmationScreen(Screen):
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


class LoadingOverlay(Screen):
    """
    A reusable loading overlay widget that dims the background and displays a centered loading indicator.
    """

    BINDINGS = [
        ("escape", "dismiss", "Dismiss overlay"),
    ]

    def __init__(self, message: str = "Loading...", dim_opacity: float = 0.7) -> None:
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



