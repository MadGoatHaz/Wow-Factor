"""
Tests for CHUNK-I2: Fix ViewBestScoresScreen Search.

Verifies:
- original_all_scores is populated during data load
- Search filtering works against original_all_scores
- Clearing search restores full table
- ExportMenuScreen instantiation and export handlers
- Compose yields consolidated Export button (not 4 separate)
"""
import pytest
import inspect


class TestOriginalAllScoresInitialization:
    """Verify original_all_scores is properly initialized and populated."""

    def test_original_all_scores_initialized_empty(self):
        """original_all_scores starts as empty list on instantiation."""
        from ui.screens.views.rendering import ViewBestScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewBestScoresScreen()
        assert screen.original_all_scores == []

    def test_current_data_initialized_empty(self):
        """current_data starts as empty list on instantiation."""
        from ui.screens.views.rendering import ViewBestScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewBestScoresScreen()
        assert screen.current_data == []

    def test_original_all_scores_attribute_exists(self):
        """ViewBestScoresScreen has original_all_scores attribute."""
        from ui.screens.views.rendering import ViewBestScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewBestScoresScreen()
        assert hasattr(screen, 'original_all_scores')
        assert isinstance(screen.original_all_scores, list)


class TestSearchFilterLogic:
    """Verify the _filter_scores method logic directly."""

    def test_filter_scores_by_processor_model(self):
        """_filter_scores correctly filters by processor_model."""
        from ui.screens.views.rendering import ViewBestScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewBestScoresScreen()
        screen.original_all_scores = [
            {"processor_model": "Intel Core i7", "platform": "linux",
             "ops_per_second": 1000, "num_threads": 4, "timestamp": "2026-01-01"},
            {"processor_model": "AMD Ryzen 9", "platform": "darwin",
             "ops_per_second": 2000, "num_threads": 8, "timestamp": "2026-01-02"},
            {"processor_model": "Intel Xeon", "platform": "linux",
             "ops_per_second": 3000, "num_threads": 16, "timestamp": "2026-01-03"},
        ]
        screen.current_data = list(screen.original_all_scores)
        # Patch _update_table_with_scores to avoid needing mounted app
        screen._update_table_with_scores = lambda data: None
        screen._filter_scores("Intel")
        assert len(screen.current_data) == 2
        assert all("Intel" in s["processor_model"] for s in screen.current_data)

    def test_filter_scores_by_platform(self):
        """_filter_scores correctly filters by platform."""
        from ui.screens.views.rendering import ViewBestScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewBestScoresScreen()
        screen.original_all_scores = [
            {"processor_model": "CPU-A", "platform": "linux",
             "ops_per_second": 1000, "num_threads": 4, "timestamp": "2026-01-01"},
            {"processor_model": "CPU-B", "platform": "darwin",
             "ops_per_second": 2000, "num_threads": 8, "timestamp": "2026-01-02"},
            {"processor_model": "CPU-C", "platform": "linux",
             "ops_per_second": 3000, "num_threads": 16, "timestamp": "2026-01-03"},
        ]
        screen.current_data = list(screen.original_all_scores)
        screen._update_table_with_scores = lambda data: None
        screen._filter_scores("darwin")
        assert len(screen.current_data) == 1
        assert screen.current_data[0]["platform"] == "darwin"

    def test_filter_scores_case_insensitive(self):
        """Search filtering is case insensitive."""
        from ui.screens.views.rendering import ViewBestScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewBestScoresScreen()
        screen.original_all_scores = [
            {"processor_model": "Intel Core i7", "platform": "Linux",
             "ops_per_second": 1000, "num_threads": 4, "timestamp": "2026-01-01"},
        ]
        screen.current_data = list(screen.original_all_scores)
        screen._update_table_with_scores = lambda data: None

        screen._filter_scores("intel")  # lowercase
        assert len(screen.current_data) == 1
        screen._filter_scores("LINUX")  # uppercase
        assert len(screen.current_data) == 1

    def test_filter_scores_no_match(self):
        """Filtering with no matches returns empty current_data."""
        from ui.screens.views.rendering import ViewBestScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewBestScoresScreen()
        screen.original_all_scores = [
            {"processor_model": "CPU-A", "platform": "linux",
             "ops_per_second": 1000, "num_threads": 4, "timestamp": "2026-01-01"},
        ]
        screen.current_data = list(screen.original_all_scores)
        screen._update_table_with_scores = lambda data: None
        screen._filter_scores("nonexistent")
        assert len(screen.current_data) == 0

    def test_filter_scores_clear_restores_full_dataset(self):
        """Clearing search (empty string) restores full dataset."""
        from ui.screens.views.rendering import ViewBestScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewBestScoresScreen()
        screen.original_all_scores = [
            {"processor_model": "CPU-A", "platform": "linux",
             "ops_per_second": 1000, "num_threads": 4, "timestamp": "2026-01-01"},
            {"processor_model": "CPU-B", "platform": "darwin",
             "ops_per_second": 2000, "num_threads": 8, "timestamp": "2026-01-02"},
        ]
        screen.current_data = list(screen.original_all_scores)
        # Track calls to _update_table_with_scores
        update_calls = []
        screen._update_table_with_scores = lambda data: update_calls.append(data)
        # Filter down to 1
        screen._filter_scores("darwin")
        assert len(screen.current_data) == 1
        # Clear search
        screen._filter_scores("")
        assert len(screen.current_data) == 2
        # Verify _update_table_with_scores was called with full data on clear
        assert len(update_calls) >= 1
        assert len(update_calls[-1]) == 2

    def test_filter_scores_does_not_mutate_original(self):
        """Filtering does not mutate original_all_scores."""
        from ui.screens.views.rendering import ViewBestScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewBestScoresScreen()
        screen.original_all_scores = [
            {"processor_model": "CPU-A", "platform": "linux",
             "ops_per_second": 1000, "num_threads": 4, "timestamp": "2026-01-01"},
            {"processor_model": "CPU-B", "platform": "darwin",
             "ops_per_second": 2000, "num_threads": 8, "timestamp": "2026-01-02"},
        ]
        screen.current_data = list(screen.original_all_scores)
        screen._update_table_with_scores = lambda data: None
        original_ids = {id(s) for s in screen.original_all_scores}
        screen._filter_scores("darwin")
        # original_all_scores should not be mutated
        assert len(screen.original_all_scores) == 2
        assert {id(s) for s in screen.original_all_scores} == original_ids


class TestFilterUsesOriginalAllScores:
    """Verify _filter_scores reads from original_all_scores, not current_data."""

    def test_filter_uses_original_all_scores(self):
        """_filter_scores filters from original_all_scores, not current_data."""
        from ui.screens.views.rendering import ViewBestScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewBestScoresScreen()
        screen.original_all_scores = [
            {"processor_model": "CPU-A", "platform": "linux",
             "ops_per_second": 1000, "num_threads": 4, "timestamp": "2026-01-01"},
            {"processor_model": "CPU-B", "platform": "darwin",
             "ops_per_second": 2000, "num_threads": 8, "timestamp": "2026-01-02"},
        ]
        # current_data is different from original (simulating prior filter)
        screen.current_data = [
            {"processor_model": "CPU-A", "platform": "linux",
             "ops_per_second": 1000, "num_threads": 4, "timestamp": "2026-01-01"},
        ]
        screen._update_table_with_scores = lambda data: None
        # Even though current_data only has CPU-A, filtering "darwin"
        # should work because it uses original_all_scores
        screen._filter_scores("darwin")
        assert len(screen.current_data) == 1
        assert screen.current_data[0]["processor_model"] == "CPU-B"


class TestExportMenuScreen:
    """Verify ExportMenuScreen instantiation and export handlers."""

    def test_export_menu_screen_instantiation(self):
        """ExportMenuScreen can be instantiated with data."""
        from ui.screens.views.rendering import ExportMenuScreen
        data = [{"key": "value"}]
        menu = ExportMenuScreen(data)
        assert menu.data == data

    def test_export_menu_screen_has_bindings(self):
        """ExportMenuScreen has keybindings for each export format."""
        from ui.screens.views.rendering import ExportMenuScreen
        menu = ExportMenuScreen([])
        # BINDINGS is a list of tuples: (key, action_name, description)
        binding_keys = [b[0] for b in menu.BINDINGS]
        assert "1" in binding_keys   # CSV
        assert "2" in binding_keys   # JSON
        assert "3" in binding_keys   # XML
        assert "4" in binding_keys   # YAML
        assert "escape" in binding_keys  # Close

    def test_export_menu_screen_has_export_csv_action(self):
        """ExportMenuScreen has action_export_csv method."""
        from ui.screens.views.rendering import ExportMenuScreen
        menu = ExportMenuScreen([])
        assert hasattr(menu, 'action_export_csv')
        assert callable(menu.action_export_csv)

    def test_export_menu_screen_has_export_json_action(self):
        """ExportMenuScreen has action_export_json method."""
        from ui.screens.views.rendering import ExportMenuScreen
        menu = ExportMenuScreen([])
        assert hasattr(menu, 'action_export_json')
        assert callable(menu.action_export_json)

    def test_export_menu_screen_has_export_xml_action(self):
        """ExportMenuScreen has action_export_xml method."""
        from ui.screens.views.rendering import ExportMenuScreen
        menu = ExportMenuScreen([])
        assert hasattr(menu, 'action_export_xml')
        assert callable(menu.action_export_xml)

    def test_export_menu_screen_has_export_yaml_action(self):
        """ExportMenuScreen has action_export_yaml method."""
        from ui.screens.views.rendering import ExportMenuScreen
        menu = ExportMenuScreen([])
        assert hasattr(menu, 'action_export_yaml')
        assert callable(menu.action_export_yaml)

    def test_export_menu_screen_has_close_action(self):
        """ExportMenuScreen has action_close method."""
        from ui.screens.views.rendering import ExportMenuScreen
        menu = ExportMenuScreen([])
        assert hasattr(menu, 'action_close')
        assert callable(menu.action_close)

    def test_export_menu_screen_inherits_screen(self):
        """ExportMenuScreen inherits from Screen."""
        from textual.screen import Screen
        from ui.screens.views.rendering import ExportMenuScreen
        assert issubclass(ExportMenuScreen, Screen)


class TestConsolidatedExportButton:
    """Verify the export buttons are consolidated into one."""

    def test_compose_source_has_single_export_button(self):
        """compose() source code yields a single Export button."""
        from ui.screens.views.rendering import ViewBestScoresScreen
        source = inspect.getsource(ViewBestScoresScreen.compose)
        # Should have single "Export" button
        assert '"Export"' in source or "'Export'" in source
        # Should NOT have individual format export buttons
        assert "Export CSV" not in source
        assert "Export JSON" not in source
        assert "Export XML" not in source
        assert "Export YAML" not in source

    def test_on_button_pressed_handles_export(self):
        """on_button_pressed handles the consolidated export button."""
        from ui.screens.views.rendering import ViewBestScoresScreen
        source = inspect.getsource(ViewBestScoresScreen.on_button_pressed)
        assert "export" in source.lower()
        # Should reference ExportMenuScreen
        assert "ExportMenuScreen" in source

    def test_no_individual_export_button_handlers(self):
        """on_button_pressed does not handle individual export buttons."""
        from ui.screens.views.rendering import ViewBestScoresScreen
        source = inspect.getsource(ViewBestScoresScreen.on_button_pressed)
        assert "export_csv" not in source
        assert "export_json" not in source
        assert "export_xml" not in source
        assert "export_yaml" not in source

    def test_export_menu_reexported(self):
        """ExportMenuScreen is re-exported from ui.screens.views."""
        from ui.screens.views import ExportMenuScreen
        assert ExportMenuScreen is not None


class TestViewBestScoresScreenStructure:
    """Verify ViewBestScoresScreen structural properties."""

    def test_inherits_basescreen(self):
        """ViewBestScoresScreen inherits from BaseScreen."""
        from ui.screens.views.rendering import ViewBestScoresScreen
        from ui.screens.base_screen import BaseScreen
        assert issubclass(ViewBestScoresScreen, BaseScreen)

    def test_has_navigation_property(self):
        """ViewBestScoresScreen has navigation property from BaseScreen."""
        from ui.screens.views.rendering import ViewBestScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewBestScoresScreen()
        assert hasattr(screen, 'navigation')

    def test_has_filter_scores_method(self):
        """ViewBestScoresScreen has _filter_scores method."""
        from ui.screens.views.rendering import ViewBestScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewBestScoresScreen()
        assert hasattr(screen, '_filter_scores')
        assert callable(screen._filter_scores)

    def test_no_export_to_csv_method(self):
        """Dead export_to_csv method has been removed."""
        from ui.screens.views.rendering import ViewBestScoresScreen
        assert not hasattr(ViewBestScoresScreen, 'export_to_csv')

    def test_load_data_stores_original_scores(self):
        """load_data method source code stores original_all_scores."""
        from ui.screens.views.rendering import ViewBestScoresScreen
        source = inspect.getsource(ViewBestScoresScreen.load_data)
        assert "original_all_scores" in source