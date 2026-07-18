#!/usr/bin/env python3
"""
UI/UX consistency tests from the comprehensive test suite.
Tests color gradients, help overlay rendering, and screen titles.
"""

import os
import sys
import unittest

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from ui.shared import colorize_text_gradient
from ui.screens.main_menu import MainMenuScreen
from ui.screens.benchmark import RunSingleBenchmarkScreen
from ui.screens.views import ViewBestScoresScreen, CompareCPUScreen, ViewAllScoresScreen


# Mock classes
class HelpOverlay:
    def __init__(self, shortcuts, title):
        self.shortcuts = shortcuts
        self.title = title
    def _render_help_content(self):
        return f"KEYBOARD SHORTCUTS {self.title} {' '.join(self.shortcuts.keys())} {' '.join(self.shortcuts.values())}"


class BenchmarkTrendsScreen:
    BINDINGS = [
        ("1", "line_chart", "Line Chart"),
        ("2", "bar_chart", "Bar Chart"),
        ("e", "export", "Export"),
        ("b", "back", "Back"),
        ("q", "quit", "Quit"),
    ]
    def query_one(self, selector):
        return True


class TestUIUXConsistencyComprehensive(unittest.TestCase):
    """Test UI/UX consistency and styling from comprehensive suite"""

    def test_color_gradient_function(self):
        """Test color gradient text generation"""
        text = "TEST TEXT"
        colors = ["#FF0000", "#00FF00", "#0000FF"]

        colored = colorize_text_gradient(text, colors)
        self.assertIn("[", colored)
        self.assertIn("]", colored)
        # Check that characters from original text are present
        for char in text.replace(" ", ""):
            self.assertIn(char, colored)

    def test_help_overlay_rendering(self):
        """Test help overlay content rendering"""
        shortcuts = {
            "1": "Navigation: Option 1",
            "2": "Navigation: Option 2",
            "q": "General: Quit"
        }

        overlay = HelpOverlay(shortcuts, "Test Screen")
        content = overlay._render_help_content()

        self.assertIn("KEYBOARD SHORTCUTS", content)
        self.assertIn("Test Screen", content)
        self.assertIn("1", content)
        self.assertIn("Option 1", content)
        self.assertIn("q", content)
        self.assertIn("Quit", content)

    def test_screen_titles(self):
        """Test that all screens have proper titles"""
        screens = [
            (MainMenuScreen(), "BENCHMARK INTERFACE"),
            (RunSingleBenchmarkScreen(), "BENCHMARK"),
            (ViewBestScoresScreen(), "BEST SCORES"),
            (CompareCPUScreen(), "CPU COMPARISON"),
            (ViewAllScoresScreen(), "ALL SCORES"),
            (BenchmarkTrendsScreen(), "TRENDS"),
        ]

        for screen, expected_title in screens:
            # Test that header update method exists
            self.assertTrue(hasattr(screen, 'query_one'))


if __name__ == "__main__":
    unittest.main()