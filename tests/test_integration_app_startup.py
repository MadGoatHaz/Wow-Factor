"""Integration tests for app startup, CSS parsing, and screen initialization.

These tests verify the application can START and basic initialization works.
They catch bugs that unit tests miss: invalid CSS, missing screens, broken compose,
and navigation initialization failures.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

project_root = Path(__file__).parent.parent


class TestCSSParsing:
    """Tests verifying the CSS file is valid and parseable."""

    def test_css_parses_without_error(self):
        """TCSS file must parse without raising StylesheetParseError.

        Catches the bug where CSS contains invalid syntax that only manifests
        at Textual runtime, not at import time.
        """
        from textual.css.stylesheet import Stylesheet

        ss = Stylesheet()
        css_path = project_root / "ui" / "styles.tcss"
        ss.read(str(css_path))

        rules = list(ss.rules)
        assert len(rules) > 0, "TCSS must have at least one parseable rule"

    def test_css_has_minimum_rules(self):
        """TCSS file must contain a meaningful number of style rules."""
        from textual.css.stylesheet import Stylesheet

        ss = Stylesheet()
        css_path = project_root / "ui" / "styles.tcss"
        ss.read(str(css_path))

        rules = list(ss.rules)
        assert len(rules) >= 5, f"Expected at least 5 CSS rules, got {len(rules)}"

    def test_no_python_docstring_in_tcss(self):
        """TCSS file must not start with a Python triple-quote docstring.

        Catches the bug where the CSS file accidentally contains a Python
        docstring block.
        """
        css_path = project_root / "ui" / "styles.tcss"
        with open(css_path) as f:
            content = f.read().strip()

        for line in content.split('\n'):
            stripped = line.strip()
            if not stripped.startswith('//') and stripped:
                assert not stripped.startswith('"""'), \
                    f"TCSS file must not start with Python docstring. First non-comment line: {stripped}"
                break

    def test_tcss_file_exists_and_is_not_empty(self):
        """The TCSS file must exist and contain content."""
        css_path = project_root / "ui" / "styles.tcss"
        assert css_path.exists(), "TCSS file must exist at ui/styles.tcss"
        assert css_path.stat().st_size > 0, "TCSS file must not be empty"


class TestAppInstantiation:
    """Tests verifying the WowFactorTUI app creates correctly."""

    def test_app_creates_without_error(self):
        """App instantiates with no exceptions."""
        from ui.app import WowFactorTUI

        app = WowFactorTUI()
        assert app is not None
        assert hasattr(app, 'navigation')
        assert hasattr(app, 'layout_manager')

    def test_app_has_css_path(self):
        """App.CSS_PATH points to 'styles.tcss' (relative path)."""
        from ui.app import WowFactorTUI

        assert WowFactorTUI.CSS_PATH == "styles.tcss"

    def test_app_has_all_required_screen_types(self):
        """All 12 expected screens are registered in SCREENS dict."""
        from ui.app import WowFactorTUI

        expected = {
            "main_menu", "run_single_benchmark", "run_batch_benchmark",
            "view_best_scores", "compare_cpu", "view_all_scores",
            "clear_invalid_confirm", "clear_invalid_result",
            "profile_selection", "analytics", "trends_chart",
            "loading_overlay",
        }
        assert expected.issubset(set(WowFactorTUI.SCREENS.keys()))
        assert len(WowFactorTUI.SCREENS) == 12

    def test_app_has_navigation_manager(self):
        """App instance creates with a NavigationManager attached."""
        from ui.app import WowFactorTUI

        app = WowFactorTUI()
        nav = app.navigation
        assert nav is not None
        assert type(nav).__name__ == "NavigationManager"


class TestScreenImport:
    """Tests verifying all screen classes can be imported and instantiated."""

    def test_main_menu_import_and_instantiate(self):
        """MainMenuScreen can be imported and instantiated."""
        from ui.screens.main_menu import MainMenuScreen

        screen = MainMenuScreen()
        assert screen is not None

    def test_benchmark_screens_import_and_instantiate(self):
        """Both benchmark screens can be imported and instantiated."""
        from ui.screens.benchmark import RunSingleBenchmarkScreen, RunBatchBenchmarkScreen

        s1 = RunSingleBenchmarkScreen()
        s2 = RunBatchBenchmarkScreen()
        assert s1 is not None
        assert s2 is not None

    def test_view_screens_import_and_instantiate(self):
        """All view screens can be imported and instantiated."""
        from ui.screens.views import ViewBestScoresScreen, CompareCPUScreen, ViewAllScoresScreen

        s1 = ViewBestScoresScreen()
        s2 = CompareCPUScreen()
        s3 = ViewAllScoresScreen()
        assert s1 is not None
        assert s2 is not None
        assert s3 is not None

    def test_analytics_screens_import_and_instantiate(self):
        """Analytics screens can be imported and instantiated."""
        from ui.screens.analytics import AnalyticsScreen, TrendsChartScreen

        s1 = AnalyticsScreen()
        s2 = TrendsChartScreen()
        assert s1 is not None
        assert s2 is not None

    def test_loading_overlay_import_and_instantiate(self):
        """LoadingOverlay can be imported and instantiated."""
        from ui.shared import LoadingOverlay

        overlay = LoadingOverlay(message="test")
        assert overlay is not None
        assert overlay.message == "test"

    def test_clear_invalid_screens_import_and_instantiate(self):
        """ClearInvalid scores screens can be imported and instantiated."""
        from ui.shared import ClearInvalidScoresConfirmationScreen
        from ui.screens.cleanup import ClearInvalidScoresResultScreen

        s1 = ClearInvalidScoresConfirmationScreen(invalid_count=3)
        s2 = ClearInvalidScoresResultScreen(deleted_count=2)
        assert s1 is not None
        assert s2 is not None
        assert s1.invalid_count == 3
        assert s2.deleted_count == 2


class TestNavigationInitialization:
    """Tests verifying navigation manager initializes correctly."""

    def test_nav_manager_singleton_behavior(self):
        """Multiple NavigationManager() calls return the same instance."""
        from ui.navigation import NavigationManager

        NavigationManager._instance = None
        NavigationManager._app = None

        nav1 = NavigationManager()
        nav2 = NavigationManager()
        assert nav1 is nav2, "NavigationManager must be a singleton"

    def test_nav_manager_requires_initialize(self):
        """NavigationManager.app property raises RuntimeError before initialize()."""
        from ui.navigation import NavigationManager

        NavigationManager._instance = None
        NavigationManager._app = None

        nav = NavigationManager()
        with pytest.raises(RuntimeError, match="not initialized"):
            _ = nav.app

    def test_nav_manager_initialize_sets_app(self):
        """After initialize(), nav.app returns the app."""
        from ui.navigation import NavigationManager

        NavigationManager._instance = None
        NavigationManager._app = None

        nav = NavigationManager()
        mock_app = MagicMock()
        mock_app.SCREENS = {"main_menu": MagicMock}
        nav.initialize(mock_app)
        assert nav.app is mock_app

    def test_nav_manager_go_back_no_crash_with_empty_stack(self):
        """go_back must not crash when app.screen_stack is empty."""
        from ui.navigation import NavigationManager

        NavigationManager._instance = None
        NavigationManager._app = None

        nav = NavigationManager()
        mock_app = MagicMock()
        mock_app.screen_stack = []
        mock_app.SCREENS = {"main_menu": MagicMock}
        nav.initialize(mock_app)

        nav.go_back()

    def test_nav_manager_go_back_no_crash_with_one_screen(self):
        """go_back must not crash when only one screen is on the stack."""
        from ui.navigation import NavigationManager

        NavigationManager._instance = None
        NavigationManager._app = None

        nav = NavigationManager()
        mock_app = MagicMock()
        mock_app.screen_stack = [MagicMock()]
        mock_app.SCREENS = {"main_menu": MagicMock}
        nav.initialize(mock_app)

        nav.go_back()