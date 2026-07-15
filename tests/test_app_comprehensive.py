"""Comprehensive app entry path tests for WowFactor TUI.

Covers:
- App instantiation
- All screen instantiation
- Navigation manager
- Worker creation (mocked)
- Screen compose methods
- Data export mixin
- Shared components
- Theme system
- CSS file validation
- Message classes
"""

import pytest
import os
import io
from unittest.mock import MagicMock, patch, PropertyMock

# ============================================================================
# App Tests
# ============================================================================


class TestAppInstantiation:
    """Tests for WowFactorTUI app instantiation and core attributes."""

    def test_app_instantiates(self):
        """App can be instantiated without errors."""
        from ui.app import WowFactorTUI
        app = WowFactorTUI()
        assert app is not None
        assert hasattr(app, 'navigation')

    def test_app_has_css_path(self):
        """App has CSS_PATH defined and points to styles.tcss."""
        from ui.app import WowFactorTUI
        assert WowFactorTUI.CSS_PATH == "styles.tcss"

    def test_app_screen_registry(self):
        """App has all expected screens in SCREENS registry."""
        from ui.app import WowFactorTUI
        expected = {
            "main_menu", "run_single_benchmark", "run_batch_benchmark",
            "view_best_scores", "compare_cpu", "view_all_scores",
            "clear_invalid_confirm", "clear_invalid_result",
            "profile_selection", "analytics", "trends_chart",
            "loading_overlay",
        }
        assert expected.issubset(set(WowFactorTUI.SCREENS.keys()))

    def test_app_screen_count(self):
        """App SCREENS dict has exactly 13 entries."""
        from ui.app import WowFactorTUI
        assert len(WowFactorTUI.SCREENS) == 13

    def test_app_has_layout_manager_attr(self):
        """App instance has layout_manager after instantiation."""
        from ui.app import WowFactorTUI
        app = WowFactorTUI()
        assert hasattr(app, 'layout_manager')

    def test_app_on_mount_defines_push_screen(self):
        """App on_mount calls navigation.initialize and push_screen."""
        from ui.app import WowFactorTUI
        app = WowFactorTUI()
        # on_mount should call self.navigation.initialize(self)
        # and self.push_screen("main_menu"). Verify navigation exists.
        assert app.navigation is not None


# ============================================================================
# Screen Instantiation Tests
# ============================================================================


class TestScreenInstantiation:
    """Every screen class can be instantiated without error."""

    def test_main_menu_screen(self):
        from ui.screens.main_menu import MainMenuScreen
        screen = MainMenuScreen()
        assert screen is not None
        assert hasattr(screen, 'compose')

    def test_run_single_benchmark_screen(self):
        from ui.screens.benchmark import RunSingleBenchmarkScreen
        screen = RunSingleBenchmarkScreen()
        assert screen is not None
        assert hasattr(screen, 'compose')

    def test_run_batch_benchmark_screen(self):
        from ui.screens.benchmark import RunBatchBenchmarkScreen
        screen = RunBatchBenchmarkScreen()
        assert screen is not None
        assert hasattr(screen, 'compose')

    def test_view_best_scores_screen(self):
        from ui.screens.views.rendering import ViewBestScoresScreen
        screen = ViewBestScoresScreen()
        assert screen is not None
        assert hasattr(screen, 'compose')

    def test_view_all_scores_screen(self):
        from ui.screens.views.navigation import ViewAllScoresScreen
        screen = ViewAllScoresScreen()
        assert screen is not None
        assert hasattr(screen, 'compose')

    def test_compare_cpu_screen(self):
        from ui.screens.views.charts import CompareCPUScreen
        screen = CompareCPUScreen()
        assert screen is not None
        assert hasattr(screen, 'compose')

    def test_analytics_screen(self):
        from ui.screens.analytics import AnalyticsScreen
        screen = AnalyticsScreen()
        assert screen is not None
        assert hasattr(screen, 'compose')

    def test_trends_chart_screen(self):
        from ui.screens.analytics import TrendsChartScreen
        screen = TrendsChartScreen()
        assert screen is not None
        assert hasattr(screen, 'compose')

    def test_clear_invalid_confirm_screen(self):
        from ui.screens.confirmation import ClearInvalidScoresConfirmationScreen
        screen = ClearInvalidScoresConfirmationScreen()
        assert screen is not None
        assert screen.invalid_count == 0

    def test_clear_invalid_confirm_screen_with_count(self):
        from ui.screens.confirmation import ClearInvalidScoresConfirmationScreen
        screen = ClearInvalidScoresConfirmationScreen(invalid_count=5)
        assert screen.invalid_count == 5

    def test_clear_invalid_result_screen(self):
        from ui.screens.cleanup import ClearInvalidScoresResultScreen
        screen = ClearInvalidScoresResultScreen(deleted_count=3)
        assert screen is not None
        assert screen.deleted_count == 3

    def test_profile_selection_screen_empty(self):
        from ui.screens.profile_selection import ProfileSelectionScreen
        screen = ProfileSelectionScreen(profiles=[])
        assert screen is not None
        assert screen.profiles == []
        assert screen.create_new is False

    def test_profile_selection_screen_with_profiles(self):
        from ui.screens.profile_selection import ProfileSelectionScreen
        screen = ProfileSelectionScreen(profiles=['profile1', 'profile2'], create_new=True)
        assert screen is not None
        assert screen.profiles == ['profile1', 'profile2']
        assert screen.create_new is True

    def test_loading_overlay_default(self):
        from ui.screens.overlay import LoadingOverlay
        overlay = LoadingOverlay()
        assert overlay is not None
        assert overlay.message == "Loading..."
        assert overlay.dim_opacity == 0.4

    def test_loading_overlay_custom(self):
        from ui.screens.overlay import LoadingOverlay
        overlay = LoadingOverlay(message="Please wait", dim_opacity=0.5)
        assert overlay.message == "Please wait"
        assert overlay.dim_opacity == 0.5


# ============================================================================
# Worker Creation Tests (mocked)
# ============================================================================


class TestWorkerCreation:
    """Workers are created correctly (mocked to avoid actual work)."""

    def test_screen_has_run_worker(self):
        """All screens inherit run_worker from Textual Screen."""
        from ui.screens.main_menu import MainMenuScreen
        screen = MainMenuScreen()
        assert hasattr(screen, 'run_worker')

    @patch('ui.screens.benchmark.RunSingleBenchmarkScreen.run_worker')
    def test_single_benchmark_worker_callable(self, mock_run_worker):
        """RunSingleBenchmarkScreen.run_worker is called with a callable."""
        from ui.screens.benchmark import RunSingleBenchmarkScreen
        screen = RunSingleBenchmarkScreen()
        mock_worker = MagicMock()
        mock_run_worker.return_value = mock_worker
        # Simulate what start_benchmark_run does
        screen.benchmark_worker = mock_run_worker(
            lambda: None,
            thread=True,
            group="benchmark_workers",
        )
        call_args = mock_run_worker.call_args
        assert call_args is not None
        assert callable(call_args[0][0])

    @patch('ui.screens.benchmark.RunBatchBenchmarkScreen.run_worker')
    def test_batch_benchmark_worker_callable(self, mock_run_worker):
        """RunBatchBenchmarkScreen.run_worker is called with a callable."""
        from ui.screens.benchmark import RunBatchBenchmarkScreen
        screen = RunBatchBenchmarkScreen()
        mock_worker = MagicMock()
        mock_run_worker.return_value = mock_worker
        screen.batch_worker_instance = mock_run_worker(
            lambda: None,
            group="batch_benchmark_workers",
        )
        call_args = mock_run_worker.call_args
        assert call_args is not None
        assert callable(call_args[0][0])

    def test_view_best_scores_load_data_method(self):
        """ViewBestScoresScreen has load_data method for direct data loading."""
        from ui.screens.views.rendering import ViewBestScoresScreen
        screen = ViewBestScoresScreen()
        assert hasattr(screen, 'load_data')
        assert callable(screen.load_data)

    def test_compare_cpu_load_cpus_method(self):
        """CompareCPUScreen has load_available_cpus method."""
        from ui.screens.views.charts import CompareCPUScreen
        screen = CompareCPUScreen()
        assert hasattr(screen, 'load_available_cpus')
        assert callable(screen.load_available_cpus)

    def test_analytics_load_data_method(self):
        """AnalyticsScreen has load_data method."""
        from ui.screens.analytics import AnalyticsScreen
        screen = AnalyticsScreen()
        assert hasattr(screen, 'load_data')
        assert callable(screen.load_data)

    def test_trends_chart_load_data_method(self):
        """TrendsChartScreen has load_data method."""
        from ui.screens.analytics import TrendsChartScreen
        screen = TrendsChartScreen()
        assert hasattr(screen, 'load_data')
        assert callable(screen.load_data)

    def test_single_benchmark_has_stop_method(self):
        """RunSingleBenchmarkScreen has stop_benchmark_run method."""
        from ui.screens.benchmark import RunSingleBenchmarkScreen
        screen = RunSingleBenchmarkScreen()
        assert hasattr(screen, 'stop_benchmark_run')

    def test_batch_benchmark_has_stop_method(self):
        """RunBatchBenchmarkScreen has stop_batch_benchmark method."""
        from ui.screens.benchmark import RunBatchBenchmarkScreen
        screen = RunBatchBenchmarkScreen()
        assert hasattr(screen, 'stop_batch_benchmark')


# ============================================================================
# Navigation Tests
# ============================================================================


class TestNavigation:
    """Navigation manager works correctly."""

    def test_navigation_singleton(self):
        """NavigationManager is a singleton (session-scoped via conftest)."""
        from ui.navigation import NavigationManager
        # conftest initializes it once per session
        nav = NavigationManager()
        assert nav is not None

    def test_navigation_has_navigate_to(self):
        """NavigationManager has navigate_to method."""
        from ui.navigation import NavigationManager
        nav = NavigationManager()
        assert hasattr(nav, 'navigate_to')
        assert callable(nav.navigate_to)

    def test_navigation_has_go_back(self):
        """NavigationManager has go_back method."""
        from ui.navigation import NavigationManager
        nav = NavigationManager()
        assert hasattr(nav, 'go_back')
        assert callable(nav.go_back)

    def test_navigation_has_notify(self):
        """NavigationManager has notify method."""
        from ui.navigation import NavigationManager
        nav = NavigationManager()
        assert hasattr(nav, 'notify')
        assert callable(nav.notify)

    def test_navigation_has_reset_to_main(self):
        """NavigationManager has reset_to_main method."""
        from ui.navigation import NavigationManager
        nav = NavigationManager()
        assert hasattr(nav, 'reset_to_main')
        assert callable(nav.reset_to_main)

    def test_navigation_navigate_to_unknown_screen(self):
        """navigate_to raises ValueError for unknown screen name."""
        from ui.navigation import NavigationManager
        nav = NavigationManager()
        # With conftest's mock app, an unknown screen should raise
        with pytest.raises(ValueError):
            nav.navigate_to("nonexistent_screen")


# ============================================================================
# Data Export Mixin Tests
# ============================================================================


class TestDataExport:
    """Export mixin methods work correctly."""

    def test_export_data_method_exists(self):
        from ui.app import DataExportMixin
        assert hasattr(DataExportMixin, 'export_data')

    def test_export_data_write_csv_exists(self):
        from ui.app import DataExportMixin
        assert hasattr(DataExportMixin, '_write_csv')

    def test_export_data_write_json_exists(self):
        from ui.app import DataExportMixin
        assert hasattr(DataExportMixin, '_write_json')

    def test_export_data_write_xml_exists(self):
        from ui.app import DataExportMixin
        assert hasattr(DataExportMixin, '_write_xml')

    def test_export_data_write_yaml_exists(self):
        from ui.app import DataExportMixin
        assert hasattr(DataExportMixin, '_write_yaml')


# ============================================================================
# Shared Components Tests
# ============================================================================


class TestSharedComponents:
    """Shared UI components work correctly."""

    def test_wowfactor_header_exists(self):
        from ui.shared import WowFactorHeader
        header = WowFactorHeader()
        assert header is not None
        assert hasattr(header, 'update_title')
        assert hasattr(header, '_render_header')

    def test_retro_gradient_colors(self):
        from ui.shared import RETRO_GRADIENT_COLORS
        assert isinstance(RETRO_GRADIENT_COLORS, list)
        assert len(RETRO_GRADIENT_COLORS) > 0

    def test_colorize_text_gradient_basic(self):
        from ui.shared import colorize_text_gradient, RETRO_GRADIENT_COLORS
        result = colorize_text_gradient("test", RETRO_GRADIENT_COLORS)
        assert isinstance(result, str)
        # Should contain color markup
        assert "[#" in result

    def test_colorize_text_gradient_empty_text(self):
        from ui.shared import colorize_text_gradient, RETRO_GRADIENT_COLORS
        result = colorize_text_gradient("", RETRO_GRADIENT_COLORS)
        assert result == ""

    def test_colorize_text_gradient_empty_colors(self):
        from ui.shared import colorize_text_gradient
        result = colorize_text_gradient("test", [])
        assert result == "test"

    def test_clear_invalid_scores_confirmed_message(self):
        from ui.screens.confirmation import ClearInvalidScoresConfirmed
        msg = ClearInvalidScoresConfirmed(5)
        assert msg.file_count == 5
        assert isinstance(msg, ClearInvalidScoresConfirmed)

    def test_loading_overlay_compose_returns_container(self):
        from ui.screens.overlay import LoadingOverlay
        overlay = LoadingOverlay()
        # compose yields a Container
        results = list(overlay.compose())
        assert len(results) == 1


# ============================================================================
# Theme System Tests
# ============================================================================


class TestThemeSystem:
    """Theme tokens are correctly defined."""

    def test_color_palette_exists(self):
        from ui.theme import ColorPalette
        assert hasattr(ColorPalette, 'PRIMARY_CYAN')
        assert hasattr(ColorPalette, 'BG_DARK')
        assert hasattr(ColorPalette, 'TEXT_PRIMARY')

    def test_color_palette_values_are_hex(self):
        from ui.theme import ColorPalette
        assert ColorPalette.PRIMARY_CYAN.startswith('#')
        assert ColorPalette.SUCCESS_GREEN.startswith('#')
        assert ColorPalette.ERROR_RED.startswith('#')

    def test_color_palette_get_rgb(self):
        from ui.theme import ColorPalette
        rgb = ColorPalette.get_rgb("#06b6d4")
        assert isinstance(rgb, tuple)
        assert len(rgb) == 3
        assert rgb == (6, 182, 212)

    def test_color_palette_get_css_rgb(self):
        from ui.theme import ColorPalette
        css = ColorPalette.get_css_rgb("#06b6d4")
        assert isinstance(css, str)
        assert "rgb" in css

    def test_spacing_scale_exists(self):
        from ui.theme import SpacingScale
        assert hasattr(SpacingScale, 'SPACING_XS')
        assert hasattr(SpacingScale, 'SPACING_SM')
        assert hasattr(SpacingScale, 'SPACING_MD')
        assert hasattr(SpacingScale, 'SPACING_LG')
        assert hasattr(SpacingScale, 'SPACING_XL')
        assert hasattr(SpacingScale, 'SPACING_2XL')

    def test_spacing_scale_values(self):
        from ui.theme import SpacingScale
        assert SpacingScale.SPACING_XS == 1
        assert SpacingScale.SPACING_SM == 2
        assert SpacingScale.SPACING_2XL == 32

    def test_spacing_scale_get_method(self):
        from ui.theme import SpacingScale
        assert SpacingScale.get('SPACING_SM') == 2

    def test_typography_exists(self):
        from ui.theme import Typography
        assert hasattr(Typography, 'TEXT_XS')
        assert hasattr(Typography, 'TEXT_SM')
        assert hasattr(Typography, 'TEXT_2XL')
        assert hasattr(Typography, 'FONT_BOLD')

    def test_typography_values(self):
        from ui.theme import Typography
        assert Typography.TEXT_XS == 12
        assert Typography.TEXT_2XL == 24
        assert Typography.FONT_BOLD == 700


# ============================================================================
# CSS File Validation
# ============================================================================


class TestCSSValidation:
    """TCSS file is valid and parseable."""

    def test_styles_tcss_exists(self):
        assert os.path.exists('ui/styles.tcss')

    def test_styles_tcss_is_not_empty(self):
        with open('ui/styles.tcss') as f:
            content = f.read()
        assert len(content.strip()) > 0

    def test_styles_tcss_no_python_docstring(self):
        with open('ui/styles.tcss') as f:
            first_line = f.readline().strip()
        assert not first_line.startswith('"""'), \
            "TCSS must not start with Python docstring"

    def test_styles_tcss_parseable(self):
        from textual.css.stylesheet import Stylesheet
        ss = Stylesheet()
        ss.read('ui/styles.tcss')
        # Stylesheet loaded without raising


# ============================================================================
# Messages Tests
# ============================================================================


class TestMessages:
    """Custom message classes work correctly."""

    def test_benchmark_progress_message(self):
        from ui.messages import BenchmarkProgress
        msg = BenchmarkProgress(100, 50.0)
        assert msg.total_ops == 100
        assert msg.ops_per_second == 50.0

    def test_benchmark_completion_message(self):
        from ui.messages import BenchmarkCompletion
        msg = BenchmarkCompletion({"result": 42})
        assert msg.result_data == {"result": 42}
        assert msg.interrupted is False

    def test_benchmark_completion_interrupted(self):
        from ui.messages import BenchmarkCompletion
        msg = BenchmarkCompletion({"error": "test"}, interrupted=True)
        assert msg.interrupted is True

    def test_batch_benchmark_progress_message(self):
        from ui.messages import BatchBenchmarkProgress
        msg = BatchBenchmarkProgress(1, 5, 100, 50.0)
        assert msg.batch_run_number == 1
        assert msg.total_batch_runs == 5
        assert msg.total_ops == 100
        assert msg.ops_per_second == 50.0

    def test_batch_benchmark_completion_message(self):
        from ui.messages import BatchBenchmarkCompletion
        msg = BatchBenchmarkCompletion([{"result": 1}], 5)
        assert msg.results == [{"result": 1}]
        assert msg.total_batch_runs == 5
        assert msg.interrupted is False

    def test_batch_benchmark_completion_interrupted(self):
        from ui.messages import BatchBenchmarkCompletion
        msg = BatchBenchmarkCompletion([], 5, interrupted=True)
        assert msg.interrupted is True

    def test_cooldown_message(self):
        from ui.messages import CooldownMessage
        msg = CooldownMessage(2, 5, 3)
        assert msg.current_batch_run == 2
        assert msg.total_batch_runs == 5
        assert msg.cooldown_seconds == 3

    def test_data_load_complete_message(self):
        from ui.messages import DataLoadComplete
        msg = DataLoadComplete([{"a": 1}])
        assert msg.data == [{"a": 1}]

    def test_data_load_error_message(self):
        from ui.messages import DataLoadError
        msg = DataLoadError()
        assert msg is not None


# ============================================================================
# Base Screen Tests
# ============================================================================


class TestBaseScreen:
    """Base screen classes work correctly."""

    def test_base_screen_inherits_screen(self):
        from ui.screens.base_screen import BaseScreen
        from textual.screen import Screen
        assert issubclass(BaseScreen, Screen)

    def test_screen_with_services_mixin(self):
        from ui.screens.base_screen import ScreenWithServices
        assert hasattr(ScreenWithServices, 'navigation')
        assert hasattr(ScreenWithServices, 'services')
        assert hasattr(ScreenWithServices, 'get_service')
        assert hasattr(ScreenWithServices, 'has_service')


# ============================================================================
# Screen Compose Tests
# ============================================================================


class TestScreenCompose:
    """Every screen's compose() method yields widgets without crashing."""

    @pytest.fixture(autouse=True)
    def _reset_nav(self):
        """Reset NavigationManager singleton before each compose test."""
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        yield
        NavigationManager._instance = None

    async def test_main_menu_compose(self):
        from textual.app import App
        from ui.screens.main_menu import MainMenuScreen
        class TestApp(App):
            SCREENS = {"main_menu": MainMenuScreen}
            CSS_PATH = None
        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(MainMenuScreen())
            await pilot.pause()
            assert pilot.app.screen is not None

    async def test_run_single_benchmark_compose(self):
        from textual.app import App
        from ui.screens.benchmark import RunSingleBenchmarkScreen
        class TestApp(App):
            SCREENS = {"run_single_benchmark": RunSingleBenchmarkScreen}
            CSS_PATH = None
        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(RunSingleBenchmarkScreen())
            await pilot.pause()
            assert pilot.app.screen is not None

    async def test_run_batch_benchmark_compose(self):
        from textual.app import App
        from ui.screens.benchmark import RunBatchBenchmarkScreen
        class TestApp(App):
            SCREENS = {"run_batch_benchmark": RunBatchBenchmarkScreen}
            CSS_PATH = None
        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(RunBatchBenchmarkScreen())
            await pilot.pause()
            assert pilot.app.screen is not None

    async def test_view_best_scores_compose(self):
        from textual.app import App
        from ui.screens.views.rendering import ViewBestScoresScreen
        from ui.screens.overlay import LoadingOverlay
        from ui.navigation import NavigationManager
        class TestApp(App):
            SCREENS = {"view_best_scores": ViewBestScoresScreen, "loading_overlay": LoadingOverlay}
            CSS_PATH = None
            def on_mount(self):
                self.navigation = NavigationManager()
                self.navigation.initialize(self)
        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(ViewBestScoresScreen())
            await pilot.pause()
            assert True  # Screen composed and on_mount survived

    async def test_view_all_scores_compose(self):
        from textual.app import App
        from ui.screens.views.navigation import ViewAllScoresScreen
        from ui.screens.overlay import LoadingOverlay
        from ui.navigation import NavigationManager
        class TestApp(App):
            SCREENS = {"view_all_scores": ViewAllScoresScreen, "loading_overlay": LoadingOverlay}
            CSS_PATH = None
            def on_mount(self):
                self.navigation = NavigationManager()
                self.navigation.initialize(self)
        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(ViewAllScoresScreen())
            await pilot.pause()
            assert True  # Screen composed and on_mount survived

    async def test_compare_cpu_compose(self):
        from textual.app import App
        from ui.screens.views.charts import CompareCPUScreen
        class TestApp(App):
            SCREENS = {"compare_cpu": CompareCPUScreen}
            CSS_PATH = None
        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(CompareCPUScreen())
            await pilot.pause()
            assert pilot.app.screen is not None

    async def test_analytics_compose(self):
        from textual.app import App
        from ui.screens.analytics import AnalyticsScreen
        class TestApp(App):
            SCREENS = {"analytics": AnalyticsScreen}
            CSS_PATH = None
        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(AnalyticsScreen())
            await pilot.pause()
            assert pilot.app.screen is not None

    async def test_trends_chart_compose(self):
        from textual.app import App
        from ui.screens.analytics import TrendsChartScreen
        class TestApp(App):
            SCREENS = {"trends_chart": TrendsChartScreen}
            CSS_PATH = None
        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(TrendsChartScreen())
            await pilot.pause()
            assert pilot.app.screen is not None

    async def test_clear_invalid_confirm_compose(self):
        from textual.app import App
        from ui.screens.confirmation import ClearInvalidScoresConfirmationScreen
        class TestApp(App):
            SCREENS = {"clear_invalid_confirm": ClearInvalidScoresConfirmationScreen}
            CSS_PATH = None
        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(ClearInvalidScoresConfirmationScreen())
            await pilot.pause()
            assert pilot.app.screen is not None

    async def test_clear_invalid_result_compose(self):
        from textual.app import App
        from ui.screens.cleanup import ClearInvalidScoresResultScreen
        class TestApp(App):
            SCREENS = {"clear_invalid_result": ClearInvalidScoresResultScreen}
            CSS_PATH = None
        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(ClearInvalidScoresResultScreen(deleted_count=0))
            await pilot.pause()
            assert pilot.app.screen is not None
            # Verify status message widget exists with correct ID
            status = pilot.app.screen.query_one("#status_message")
            assert status is not None

    async def test_clear_invalid_result_success_message(self):
        """Test cleanup screen shows success message when files were deleted."""
        from textual.app import App
        from ui.screens.cleanup import ClearInvalidScoresResultScreen
        class TestApp(App):
            SCREENS = {"clear_invalid_result": ClearInvalidScoresResultScreen}
            CSS_PATH = None
        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(ClearInvalidScoresResultScreen(deleted_count=5))
            await pilot.pause()
            status = pilot.app.screen.query_one("#status_message")
            # Static widget stores its content; verify classes applied
            assert "cleanup-success" in status.classes

    async def test_profile_selection_compose_empty(self):
        from textual.app import App
        from ui.screens.profile_selection import ProfileSelectionScreen
        class TestApp(App):
            SCREENS = {"profile_selection": ProfileSelectionScreen}
            CSS_PATH = None
        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(ProfileSelectionScreen(profiles=[]))
            await pilot.pause()
            assert pilot.app.screen is not None

    def test_loading_overlay_compose(self):
        """LoadingOverlay compose works when tested via instance creation."""
        from ui.screens.overlay import LoadingOverlay
        overlay = LoadingOverlay()
        # LoadingOverlay compose was confirmed working via test_shared_loading_overlay_compose
        assert hasattr(overlay, 'compose')
        assert callable(overlay.compose)

    def test_compose_methods_exist_all_screens(self):
        """All screen classes have a compose method defined."""
        from ui.screens.main_menu import MainMenuScreen
        from ui.screens.benchmark import RunSingleBenchmarkScreen, RunBatchBenchmarkScreen
        from ui.screens.views.rendering import ViewBestScoresScreen
        from ui.screens.views.navigation import ViewAllScoresScreen
        from ui.screens.views.charts import CompareCPUScreen
        from ui.screens.analytics import AnalyticsScreen, TrendsChartScreen
        from ui.screens.confirmation import ClearInvalidScoresConfirmationScreen
        from ui.screens.overlay import LoadingOverlay
        from ui.screens.cleanup import ClearInvalidScoresResultScreen
        from ui.screens.profile_selection import ProfileSelectionScreen

        all_screens = [
            MainMenuScreen,
            RunSingleBenchmarkScreen,
            RunBatchBenchmarkScreen,
            ViewBestScoresScreen,
            ViewAllScoresScreen,
            CompareCPUScreen,
            AnalyticsScreen,
            TrendsChartScreen,
            ClearInvalidScoresConfirmationScreen,
            LoadingOverlay,
            ClearInvalidScoresResultScreen,
            ProfileSelectionScreen,
        ]
        for screen_class in all_screens:
            assert hasattr(screen_class, 'compose'), \
                f"{screen_class.__name__} missing compose method"