#!/usr/bin/env python3
"""
Shared UI components for WowFactor TUI Application.
This module contains reusable components that don't depend on other UI modules,
avoiding circular import issues.
"""

from textual.widgets import Static
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






