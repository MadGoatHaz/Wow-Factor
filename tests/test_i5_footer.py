"""Tests for CHUNK-I5: Add Footer Widget to All Screens.

Verifies that Footer widgets are properly composed in all BaseScreen subclasses,
Footer CSS styling exists, and Footer does NOT appear in modal overlays.
"""

import inspect
import ast
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Test BaseScreen compose yields Footer
# ---------------------------------------------------------------------------

class TestBaseScreenCompose:
    """Verify BaseScreen.compose() yields Footer."""

    def test_basescreen_compose_yields_footer(self):
        """BaseScreen.compose() should yield Footer."""
        from ui.screens.base_screen import BaseScreen
        from textual.widgets import Footer

        screen = BaseScreen()
        composed = list(screen.compose())
        footer_widgets = [w for w in composed if isinstance(w, Footer)]
        assert len(footer_widgets) == 1, "BaseScreen should yield exactly one Footer"

    def test_basescreen_imports_footer(self):
        """base_screen.py should import Footer."""
        from ui.screens.base_screen import Footer  # noqa: F401
        assert Footer is not None

    def test_basescreen_compose_returns_composeresult(self):
        """BaseScreen.compose() should be annotated with ComposeResult."""
        from ui.screens.base_screen import BaseScreen
        sig = inspect.signature(BaseScreen.compose)
        assert sig.return_annotation is not inspect.Parameter.empty


# ---------------------------------------------------------------------------
# Test Footer present in every BaseScreen subclass
# ---------------------------------------------------------------------------

SCREEN_CLASSES_WITH_FOOTER = [
    # (module_path, class_name)
    ("ui.screens.main_menu", "MainMenuScreen"),
    ("ui.screens.cleanup", "ClearInvalidScoresResultScreen"),
    ("ui.screens.profile_selection", "ProfileSelectionScreen"),
    ("ui.screens.benchmark", "RunSingleBenchmarkScreen"),
    ("ui.screens.benchmark", "RunBatchBenchmarkScreen"),
    ("ui.screens.views.charts", "CompareCPUScreen"),
    ("ui.screens.views.rendering", "ViewBestScoresScreen"),
    ("ui.screens.views.navigation", "ViewAllScoresScreen"),
    ("ui.screens.analytics", "TrendsChartScreen"),
    ("ui.screens.analytics", "AnalyticsScreen"),
    ("ui.screens.confirmation", "ClearInvalidScoresConfirmationScreen"),
]

SCREENS_WITHOUT_FOOTER = [
    # Modal overlays should NOT have Footer
    ("ui.screens.overlay", "LoadingOverlay"),
    ("ui.screens.views.rendering", "ExportMenuScreen"),
]


class TestScreenFooterPresence:
    """Every BaseScreen subclass should yield Footer in compose()."""

    @pytest.mark.parametrize("module_path,class_name", SCREEN_CLASSES_WITH_FOOTER)
    def test_screen_compose_yields_footer(self, module_path, class_name):
        """Each BaseScreen subclass should yield Footer in its compose method."""
        module = __import__(module_path, fromlist=[class_name])
        screen_cls = getattr(module, class_name)
        from textual.widgets import Footer

        compose_source = inspect.getsource(screen_cls.compose)
        assert "Footer" in compose_source, (
            f"{class_name}.compose() should yield Footer"
        )

    @pytest.mark.parametrize("module_path,class_name", SCREEN_CLASSES_WITH_FOOTER)
    def test_screen_imports_footer(self, module_path, class_name):
        """Each screen file should import Footer."""
        module = __import__(module_path, fromlist=[class_name])
        # Check module-level namespace for Footer
        source_file = Path(module.__file__)
        content = source_file.read_text()
        assert "Footer" in content, (
            f"{module_path} should import Footer"
        )

    @pytest.mark.parametrize("module_path,class_name", SCREENS_WITHOUT_FOOTER)
    def test_modal_screen_no_footer(self, module_path, class_name):
        """Modal overlays should NOT yield Footer."""
        module = __import__(module_path, fromlist=[class_name])
        screen_cls = getattr(module, class_name)

        compose_source = inspect.getsource(screen_cls.compose)
        assert "Footer" not in compose_source, (
            f"{class_name} is a modal overlay and should NOT yield Footer"
        )


# ---------------------------------------------------------------------------
# Test Footer CSS styling
# ---------------------------------------------------------------------------

class TestFooterCSS:
    """Verify Footer CSS rules exist in styles.tcss."""

    def test_footer_css_rule_exists(self):
        """styles.tcss should contain Footer styling rules."""
        styles_path = Path(__file__).parent.parent / "ui" / "styles.tcss"
        content = styles_path.read_text()
        assert "Footer {" in content, "styles.tcss should have Footer rule"

    def test_footer_css_uses_theme_token(self):
        """Footer styling should reference theme tokens ($variable)."""
        styles_path = Path(__file__).parent.parent / "ui" / "styles.tcss"
        content = styles_path.read_text()
        # Find the Footer section
        footer_section = content.split("Footer {")[1] if "Footer {" in content else ""
        assert "$" in footer_section, "Footer CSS should use theme tokens"


# ---------------------------------------------------------------------------
# Test BINDINGS exist on all screens (Footer reads from BINDINGS)
# ---------------------------------------------------------------------------

ALL_SCREEN_CLASSES = SCREEN_CLASSES_WITH_FOOTER + SCREENS_WITHOUT_FOOTER


class TestScreenBindings:
    """All screens should define BINDINGS so Footer can display keybindings."""

    @pytest.mark.parametrize("module_path,class_name", ALL_SCREEN_CLASSES)
    def test_screen_has_bindings(self, module_path, class_name):
        """Each screen class should define BINDINGS attribute."""
        module = __import__(module_path, fromlist=[class_name])
        screen_cls = getattr(module, class_name)
        assert hasattr(screen_cls, "BINDINGS"), (
            f"{class_name} should define BINDINGS for Footer display"
        )
        assert len(screen_cls.BINDINGS) > 0, (
            f"{class_name}.BINDINGS should not be empty"
        )


# ---------------------------------------------------------------------------
# Test BaseScreen inheritance
# ---------------------------------------------------------------------------

class TestBaseScreenInheritance:
    """Verify all target screens inherit from BaseScreen."""

    @pytest.mark.parametrize("module_path,class_name", SCREEN_CLASSES_WITH_FOOTER)
    def test_screen_inherits_basescreen(self, module_path, class_name):
        """Each screen should inherit from BaseScreen."""
        from ui.screens.base_screen import BaseScreen

        module = __import__(module_path, fromlist=[class_name])
        screen_cls = getattr(module, class_name)
        assert issubclass(screen_cls, BaseScreen), (
            f"{class_name} should inherit from BaseScreen"
        )