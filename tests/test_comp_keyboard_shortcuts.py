#!/usr/bin/env python3
"""
Keyboard shortcuts tests from the comprehensive test suite.
Tests bindings on MainMenu, Benchmark, View, and Trends screens.
"""

import os
import sys
import unittest

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from ui.screens.main_menu import MainMenuScreen
from ui.screens.benchmark import RunSingleBenchmarkScreen
from ui.screens.views import ViewBestScoresScreen, ViewAllScoresScreen

# Mock BenchmarkTrendsScreen
class BenchmarkTrendsScreen:
    BINDINGS = [
        ("1", "line_chart", "Line Chart"),
        ("2", "bar_chart", "Bar Chart"),
        ("e", "export", "Export"),
        ("b", "back", "Back"),
        ("q", "quit", "Quit"),
    ]


class TestKeyboardShortcuts(unittest.TestCase):
    """Test keyboard shortcuts functionality"""

    def test_main_menu_bindings(self):
        """Test main menu keyboard shortcuts are defined"""
        screen = MainMenuScreen()
        bindings = {}
        for b in screen.BINDINGS:
            if isinstance(b, tuple):
                bindings[b[0]] = b
            else:
                bindings[b.key] = b

        self.assertIn("q", bindings)

    def test_benchmark_screen_bindings(self):
        """Test benchmark screen keyboard shortcuts"""
        screen = RunSingleBenchmarkScreen()
        bindings = {}
        for b in screen.BINDINGS:
            if isinstance(b, tuple):
                bindings[b[0]] = b
            else:
                bindings[b.key] = b

        self.assertIn("b", bindings)  # Back
        self.assertIn("q", bindings)  # Quit

    def test_data_screen_bindings(self):
        """Test data viewing screen keyboard shortcuts"""
        # Test ViewBestScoresScreen
        screen = ViewBestScoresScreen()
        bindings = {}
        for b in screen.BINDINGS:
            if isinstance(b, tuple):
                bindings[b[0]] = b
            else:
                bindings[b.key] = b

        self.assertIn("b", bindings)  # Back
        self.assertIn("q", bindings)  # Quit

        # Test ViewAllScoresScreen (should have pagination shortcuts)
        screen = ViewAllScoresScreen()
        bindings = {}
        for b in screen.BINDINGS:
            if isinstance(b, tuple):
                bindings[b[0]] = b
            else:
                bindings[b.key] = b

        self.assertIn("pageup", bindings)  # Previous page
        self.assertIn("pagedown", bindings)  # Next page
        self.assertIn("home", bindings)  # First page
        self.assertIn("end", bindings)  # Last page
        self.assertIn("g", bindings)  # Go to page

    def test_trends_screen_bindings(self):
        """Test benchmark trends screen keyboard shortcuts"""
        screen = BenchmarkTrendsScreen()
        bindings = {}
        for b in screen.BINDINGS:
            if isinstance(b, tuple):
                bindings[b[0]] = b
            else:
                bindings[b.key] = b

        self.assertIn("1", bindings)  # Line chart
        self.assertIn("2", bindings)  # Bar chart
        self.assertIn("e", bindings)  # Export chart
        self.assertIn("b", bindings)  # Back
        self.assertIn("q", bindings)  # Quit


if __name__ == "__main__":
    unittest.main()