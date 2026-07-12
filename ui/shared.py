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
from typing import List, Dict, Any
import os

# Import constants from core
from core.benchmark import BENCHMARK_DIR, LOG_DIR, format_large_number

# Import theme system for centralized design tokens
from ui.theme import ColorPalette, SpacingScale

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


CLI_STYLESHEET = """
Screen {
    background: {ColorPalette.BG_DARKER};
    color: {ColorPalette.PRIMARY_CYAN};
}
Header {
    text-align: center;
    color: {ColorPalette.ACCENT_MAGENTA};
    background: {ColorPalette.BG_LIGHT};
    height: 3;
    content-align: center middle;
}
Container, VerticalScroll {
    margin: 0;
    padding: 0;
}
Header .subtitle {
    color: {ColorPalette.PRIMARY_CYAN};
}
Footer {
    background: {ColorPalette.BG_LIGHT};
    color: {ColorPalette.PRIMARY_CYAN};
}
Button {
    background: {ColorPalette.PRIMARY_BLUE};
    color: {ColorPalette.PRIMARY_CYAN};
    border: thick {ColorPalette.ACCENT_MAGENTA};
    width: 60%;
}
Button:hover {
    background: {ColorPalette.PRIMARY_PURPLE};
    color: {ColorPalette.ACCENT_YELLOW};
}
.main-menu-container {
    align: center middle;
}
.menu-buttons {
    align: center middle;
}
.metric-name {
    color: {ColorPalette.ACCENT_YELLOW};
}
.metric-value {
    color: {ColorPalette.SUCCESS_GREEN};
}
.gold-rank {
    color: {ColorPalette.ACCENT_ORANGE};
}
.silver-rank {
    color: {ColorPalette.TEXT_SECONDARY};
}
.bronze-rank {
    color: {ColorPalette.ACCENT_ORANGE};
}
.neon-green-rank {
    color: {ColorPalette.SUCCESS_GREEN};
}
.dark-blue-rank {
    color: {ColorPalette.TEXT_SECONDARY};
}
.loading-overlay-container {
    width: 100%;
    height: 100%;
    background: {ColorPalette.BG_DARKER};
    opacity: {self.dim_opacity};
    align: center middle;
}
.loading-message {
    color: {ColorPalette.PRIMARY_CYAN};
    text-align: center;
    padding: 1 {SpacingScale.SPACING_LG} {SpacingScale.SPACING_LG} 1;
    font-style: italic;
}
#loading-overlay {
    display: block;
}
.run-benchmark-screen {
    align: center top;
}
.run-benchmark-screen Input {
    width: 30;
    margin: {SpacingScale.SPACING_SM} 0;
    text-align: center;
    background: {ColorPalette.PRIMARY_BLUE};
    color: {ColorPalette.PRIMARY_CYAN};
    border: thick {ColorPalette.ACCENT_MAGENTA};
}
.run-benchmark-screen #progress-display {
    width: 60%;
    height: 5;
    background: {ColorPalette.BG_DARKER};
    color: {ColorPalette.SUCCESS_GREEN};
    border: tall {ColorPalette.PRIMARY_CYAN};
    margin: {SpacingScale.SPACING_SM} 0;
    text-align: center;
    overflow: hidden scroll;
}
.result-summary {
    width: 80%;
    margin: {SpacingScale.SPACING_SM} 0;
    background: {ColorPalette.BG_DARKER};
    border: solid {ColorPalette.ACCENT_MAGENTA};
    padding: {SpacingScale.SPACING_XS};
}
.result-table {
    width: 80%;
    height: auto;
    max-height: 15;
    margin: {SpacingScale.SPACING_SM} 0;
}
.search-input {
    width: 60%;
    margin: {SpacingScale.SPACING_SM} 0;
    text-align: center;
    background: {ColorPalette.PRIMARY_BLUE};
    color: {ColorPalette.PRIMARY_CYAN};
    border: thick {ColorPalette.ACCENT_MAGENTA};
}
.pagination-controls {
    width: 100%;
    height: auto;
    margin: {SpacingScale.SPACING_SM} 0;
    align: center middle;
}
.pagination-info {
    width: 100%;
    text-align: center;
    color: {ColorPalette.PRIMARY_CYAN};
    margin: {SpacingScale.SPACING_SM} 0;
}
.pagination-buttons {
    width: 100%;
    height: auto;
    align: center middle;
    margin: 0;
}
.pagination-buttons Button {
    width: 14%;
    margin: 0 {SpacingScale.SPACING_SM};
}
.export-buttons {
    width: 100%;
    height: auto;
    align: center middle;
    margin: {SpacingScale.SPACING_SM} 0;
}
.export-buttons Button {
    width: 20%;
    margin: 0 {SpacingScale.SPACING_SM};
}
.pagination-input {
    width: 10%;
    margin: 0 {SpacingScale.SPACING_SM};
    text-align: center;
    background: {ColorPalette.PRIMARY_BLUE};
    color: {ColorPalette.PRIMARY_CYAN};
    border: thick {ColorPalette.ACCENT_MAGENTA};
}
.pagination-display {
    width: 100%;
    text-align: center;
    color: {ColorPalette.PRIMARY_CYAN};
    margin: {SpacingScale.SPACING_SM} 0;
    background: {ColorPalette.BG_DARKER};
    border: solid {ColorPalette.ACCENT_MAGENTA};
    padding: {SpacingScale.SPACING_XS};
}
.action-buttons {
    width: 100%;
    height: auto;
    align: center middle;
    margin: {SpacingScale.SPACING_SM} 0;
    padding: 0;
}
.action-buttons Button {
    width: 25%;
    margin: 0 {SpacingScale.SPACING_SM};
}
.analytics-container {
    height: 1fr;
    width: 100%;
}
.compact-header {
    height: auto;
    min-height: 1;
    margin: 0 0 {SpacingScale.SPACING_SM} 0;
}
.compact-button {
    height: 3;
    min-height: 3;
    margin: 0;
}
.menu-grid {
    layout: grid;
    grid-size: 2;
    grid-gutter: {SpacingScale.SPACING_XS} {SpacingScale.SPACING_SM};
    width: 80%;
    height: auto;
    align: center middle;
    margin: {SpacingScale.SPACING_SM} 0;
}
.menu-grid Button {
    width: 100%;
}
.form-label {
    color: {ColorPalette.TEXT_PRIMARY};
    margin-bottom: {SpacingScale.SPACING_SM};
    font-weight: bold;
}
.form-input {
    width: 60%;
    margin: {SpacingScale.SPACING_SM} 0;
    text-align: center;
    background: {ColorPalette.PRIMARY_BLUE};
    color: {ColorPalette.TEXT_PRIMARY};
    border: thick {ColorPalette.ACCENT_MAGENTA};
}
.action-btn {
    width: auto;
    min-width: 10;
    margin: 0 {SpacingScale.SPACING_SM};
}
.progress-indicator {
    color: {ColorPalette.TEXT_PRIMARY};
    margin-top: {SpacingScale.SPACING_MD};
}
.results-display {
    width: 80%;
    max-height: 20;
    overflow: hidden scroll;
    background: {ColorPalette.BG_DARKER};
    border: solid {ColorPalette.BORDER_SUBTLE};
    padding: {SpacingScale.SPACING_SM};
}
.batch-indicator {
    color: {ColorPalette.ACCENT_YELLOW};
    font-weight: bold;
    margin-bottom: {SpacingScale.SPACING_SM};
}
.cooldown-display {
    color: {ColorPalette.WARNING_YELLOW};
    margin-top: {SpacingScale.SPACING_SM};
}
.command-prompt {
    color: {ColorPalette.TEXT_SECONDARY};
    font-style: italic;
    margin-top: {SpacingScale.SPACING_MD};
}
.result-message {
    color: {ColorPalette.TEXT_PRIMARY};
    text-align: center;
    padding: {SpacingScale.SPACING_SM} 0;
}
.result-message.success {
    color: {ColorPalette.SUCCESS_GREEN};
}
.result-message.info {
    color: {ColorPalette.INFO_BLUE};
}
"""
