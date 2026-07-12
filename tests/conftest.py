"""
Pytest configuration for WowFactor test suite.
Adds project root to sys.path so tests can import from core and ui modules.
Initializes NavigationManager singleton for all tests.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock
import pytest

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class MockApp:
    """Minimal mock app for NavigationManager initialization."""

    SCREENS: dict = {"loading_overlay": MagicMock}
    screen_stack: list = []
    current_screen = None

    def push_screen(self, screen):
        self.screen_stack.append(screen)
        self.current_screen = screen


@pytest.fixture(scope="session", autouse=True)
def initialize_navigation_manager():
    """Session-scoped autouse fixture to initialize NavigationManager singleton."""
    from ui.navigation import NavigationManager

    mock_app = MockApp()
    Manager = NavigationManager()
    Manager.initialize(mock_app)

    yield Manager

    # Teardown: reset singleton state
    NavigationManager._instance = None
    NavigationManager._app = None
