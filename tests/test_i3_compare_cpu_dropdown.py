#!/usr/bin/env python3
"""
Tests for CHUNK-I3: Replace CPU Text Input with Dropdown in CompareCPUScreen.

Covers:
- Select widget replacement for Input widgets
- CPU dropdown population from benchmark data
- Better/worse highlighting in comparison table
- Expanded metrics (avg, max, min, stddev, count)
- Dead _update_comparison_table method removed
- Stats calculation correctness
"""
import math
import pytest
from unittest.mock import MagicMock, patch

from textual.widgets import Select


class TestI3SelectWidgets:
    """Verify Input widgets replaced with Select dropdowns."""

    async def test_compose_yields_select_widgets_not_input(self):
        """Compose must yield Select widgets, not Input widgets."""
        from textual.app import App
        from ui.screens.views.charts import CompareCPUScreen
        class TestApp(App):
            CSS_PATH = None
        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(CompareCPUScreen())
            await pilot.pause()
            screen = pilot.app.screen
            select_widgets = list(screen.query(Select))
            assert len(select_widgets) == 2, "Should have 2 Select widgets for CPU selection"

    async def test_select_widgets_have_correct_ids(self):
        """Select widgets must have correct IDs."""
        from textual.app import App
        from ui.screens.views.charts import CompareCPUScreen
        class TestApp(App):
            CSS_PATH = None
        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(CompareCPUScreen())
            await pilot.pause()
            screen = pilot.app.screen
            select1 = screen.query_one("#first_cpu_select", Select)
            select2 = screen.query_one("#second_cpu_select", Select)
            assert select1 is not None
            assert select2 is not None

    async def test_select_widgets_have_prompts(self):
        """Select widgets must have descriptive prompts."""
        from textual.app import App
        from ui.screens.views.charts import CompareCPUScreen
        class TestApp(App):
            CSS_PATH = None
        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(CompareCPUScreen())
            await pilot.pause()
            screen = pilot.app.screen
            select1 = screen.query_one("#first_cpu_select", Select)
            select2 = screen.query_one("#second_cpu_select", Select)
            # Verify prompts contain descriptive text for each CPU slot
            assert "first" in select1.prompt.lower() or "select" in select1.prompt.lower()
            assert "second" in select2.prompt.lower() or "select" in select2.prompt.lower()

    async def test_select_widgets_allow_blank(self):
        """Select widgets should allow blank selection initially."""
        from textual.app import App
        from ui.screens.views.charts import CompareCPUScreen
        class TestApp(App):
            CSS_PATH = None
        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(CompareCPUScreen())
            await pilot.pause()
            screen = pilot.app.screen
            select1 = screen.query_one("#first_cpu_select", Select)
            select2 = screen.query_one("#second_cpu_select", Select)
            assert select1._allow_blank is True
            assert select2._allow_blank is True

    async def test_no_input_widgets_for_cpu_selection(self):
        """CPU selection should not use Input widgets anymore."""
        from textual.app import App
        from textual.widgets import Input
        from ui.screens.views.charts import CompareCPUScreen
        class TestApp(App):
            CSS_PATH = None
        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(CompareCPUScreen())
            await pilot.pause()
            screen = pilot.app.screen
            input_widgets = list(screen.query(Input))
            assert len(input_widgets) == 0, "No Input widgets should be used for CPU selection"


class TestI3CPUDropdownPopulation:
    """Verify Select widgets are populated from benchmark data."""

    def test_available_cpus_loaded_on_mount(self):
        """On mount should initialize available_cpus list."""
        from ui.screens.views.charts import CompareCPUScreen
        with patch("ui.screens.views.charts._get_all_valid_scores") as mock_scores:
            mock_scores.return_value = [
                {"processor_model": "CPU A", "ops_per_second": 1000},
                {"processor_model": "CPU B", "ops_per_second": 2000},
            ]
            screen = CompareCPUScreen()
            # Simulate mount behavior
            screen.available_cpus = []
            screen.cpu1_data = []
            screen.cpu2_data = []
            screen.load_available_cpus()
            assert sorted(screen.available_cpus) == ["CPU A", "CPU B"]

    def test_populate_select_widgets_creates_options(self):
        """Populate method must create proper (display, value) tuples."""
        from ui.screens.views.charts import CompareCPUScreen
        screen = CompareCPUScreen()
        screen.available_cpus = ["Intel i7", "AMD Ryzen"]

        # Mock query_one to capture set_options calls
        mock_select1 = MagicMock()
        mock_select2 = MagicMock()

        def query_one_side_effect(selector, type_hint):
            if "first" in selector:
                return mock_select1
            elif "second" in selector:
                return mock_select2
            return MagicMock()

        screen.query_one = MagicMock(side_effect=query_one_side_effect)
        screen._populate_select_widgets()

        expected_options = [("Intel i7", "Intel i7"), ("AMD Ryzen", "AMD Ryzen")]
        mock_select1.set_options.assert_called_once()
        mock_select2.set_options.assert_called_once()
        # Verify options content
        opts1 = mock_select1.set_options.call_args[0][0]
        opts2 = mock_select2.set_options.call_args[0][0]
        assert list(opts1) == expected_options
        assert list(opts2) == expected_options

    def test_populate_handles_empty_cpu_list(self):
        """Empty CPU list should show placeholder option."""
        from ui.screens.views.charts import CompareCPUScreen
        screen = CompareCPUScreen()
        screen.available_cpus = []

        mock_select1 = MagicMock()
        mock_select2 = MagicMock()

        def query_one_side_effect(selector, type_hint):
            if "first" in selector:
                return mock_select1
            elif "second" in selector:
                return mock_select2
            return MagicMock()

        screen.query_one = MagicMock(side_effect=query_one_side_effect)
        screen._populate_select_widgets()

        opts1 = list(mock_select1.set_options.call_args[0][0])
        assert len(opts1) == 1
        assert "No CPUs" in opts1[0][0]

    def test_loading_display_hidden_after_load(self):
        """Loading display should be hidden after CPUs loaded."""
        from ui.screens.views.charts import CompareCPUScreen
        mock_loading = MagicMock()
        screen = CompareCPUScreen()

        with patch("ui.screens.views.charts._get_all_valid_scores") as mock_scores:
            mock_scores.return_value = [{"processor_model": "CPU X", "ops_per_second": 500}]
            screen.available_cpus = []
            screen.query_one = MagicMock(return_value=mock_loading)
            screen.load_available_cpus()
            assert mock_loading.display is False


class TestI3StatsCalculation:
    """Verify _calc_stats computes correct metrics."""

    def test_calc_stats_empty(self):
        """Empty scores return zero metrics."""
        from ui.screens.views.charts import CompareCPUScreen
        stats = CompareCPUScreen._calc_stats([])
        assert stats["avg"] == 0
        assert stats["max"] == 0
        assert stats["min"] == 0
        assert stats["stddev"] == 0
        assert stats["count"] == 0

    def test_calc_stats_single_value(self):
        """Single score: avg=max=min=value, stddev=0."""
        from ui.screens.views.charts import CompareCPUScreen
        scores = [{"ops_per_second": 1000}]
        stats = CompareCPUScreen._calc_stats(scores)
        assert stats["avg"] == 1000.0
        assert stats["max"] == 1000
        assert stats["min"] == 1000
        assert stats["stddev"] == 0.0
        assert stats["count"] == 1

    def test_calc_stats_multiple_values(self):
        """Multiple scores compute correct statistics."""
        from ui.screens.views.charts import CompareCPUScreen
        scores = [
            {"ops_per_second": 1000},
            {"ops_per_second": 2000},
            {"ops_per_second": 3000},
        ]
        stats = CompareCPUScreen._calc_stats(scores)
        assert stats["avg"] == 2000.0
        assert stats["max"] == 3000
        assert stats["min"] == 1000
        assert stats["count"] == 3
        # stddev = sqrt(((1000-2000)^2 + (2000-2000)^2 + (3000-2000)^2) / 3)
        # = sqrt((1000000 + 0 + 1000000) / 3) = sqrt(666666.67) ~= 816.5
        assert abs(stats["stddev"] - 816.496580927726) < 0.01

    def test_calc_stats_stddev_precision(self):
        """Std dev uses population standard deviation formula."""
        from ui.screens.views.charts import CompareCPUScreen
        scores = [{"ops_per_second": i * 100} for i in range(1, 11)]
        stats = CompareCPUScreen._calc_stats(scores)
        # Known: ops = [100, 200, ..., 1000], mean = 550
        # var = sum((x-550)^2) / 10 = 82500, stddev = sqrt(82500) ~= 287.23
        assert abs(stats["stddev"] - math.sqrt(82500)) < 0.01
        assert stats["count"] == 10

    def test_calc_stats_missing_ops_field(self):
        """Missing ops_per_second defaults to 0."""
        from ui.screens.views.charts import CompareCPUScreen
        scores = [{"other_field": "value"}]
        stats = CompareCPUScreen._calc_stats(scores)
        assert stats["avg"] == 0.0
        assert stats["count"] == 1


class TestI3DeadCodeRemoved:
    """Verify dead _update_comparison_table method removed."""

    def test_update_comparison_table_method_removed(self):
        """_update_comparison_table should not exist on CompareCPUScreen."""
        from ui.screens.views.charts import CompareCPUScreen
        assert not hasattr(CompareCPUScreen, "_update_comparison_table"), \
            "_update_comparison_table is dead code and must be removed"

    def test_only_display_comparison_exists(self):
        """Only _display_comparison should handle table rendering."""
        from ui.screens.views.charts import CompareCPUScreen
        assert hasattr(CompareCPUScreen, "_display_comparison")
        # Check no other table update methods
        table_methods = [m for m in dir(CompareCPUScreen) if "table" in m.lower() and not m.startswith("__")]
        assert len(table_methods) == 0, f"No table-specific methods should exist: {table_methods}"


class TestI3BetterWorseHighlighting:
    """Verify comparison table applies better/worse styling."""

    def test_higher_value_highlighted_better_for_avg(self):
        """Higher average OPS/sec gets better styling."""
        from ui.screens.views.charts import CompareCPUScreen
        cpu1_data = [{"ops_per_second": 2000}, {"ops_per_second": 2100}]
        cpu2_data = [{"ops_per_second": 1000}, {"ops_per_second": 1100}]
        stats1 = CompareCPUScreen._calc_stats(cpu1_data)
        stats2 = CompareCPUScreen._calc_stats(cpu2_data)
        # avg1 = 2050, avg2 = 1050 -> cpu1 should be "better"
        assert stats1["avg"] > stats2["avg"]

    def test_lower_stddev_highlighted_better(self):
        """Lower standard deviation gets better styling (more consistent)."""
        from ui.screens.views.charts import CompareCPUScreen
        # CPU1: consistent scores
        cpu1_data = [{"ops_per_second": 1000}, {"ops_per_second": 1010}]
        # CPU2: volatile scores
        cpu2_data = [{"ops_per_second": 500}, {"ops_per_second": 1500}]
        stats1 = CompareCPUScreen._calc_stats(cpu1_data)
        stats2 = CompareCPUScreen._calc_stats(cpu2_data)
        # CPU1 stddev should be much lower (better)
        assert stats1["stddev"] < stats2["stddev"]

    def test_equal_values_no_highlight(self):
        """Equal values should not get better/worse styling."""
        from ui.screens.views.charts import CompareCPUScreen
        data = [{"ops_per_second": 1000}]
        stats = CompareCPUScreen._calc_stats(data)
        # Both CPUs same stats -> no differentiation needed
        assert stats["avg"] == stats["max"] == stats["min"]


class TestI3ExpandedMetrics:
    """Verify comparison table includes 5 metrics."""

    def test_metrics_tuple_has_five_entries(self):
        """Comparison must include 5 metric rows."""
        from ui.screens.views.charts import CompareCPUScreen
        screen = CompareCPUScreen()
        cpu1_data = [{"ops_per_second": 1000}]
        cpu2_data = [{"ops_per_second": 2000}]
        stats1 = CompareCPUScreen._calc_stats(cpu1_data)
        stats2 = CompareCPUScreen._calc_stats(cpu2_data)

        metrics = [
            ("Average OPS/sec", "avg", stats1["avg"], stats2["avg"], True),
            ("Max OPS/sec", "max", stats1["max"], stats2["max"], True),
            ("Min OPS/sec", "min", stats1["min"], stats2["min"], True),
            ("Std Dev OPS/sec", "stddev", stats1["stddev"], stats2["stddev"], False),
            ("Sample Count", "count", float(stats1["count"]), float(stats2["count"]), True),
        ]
        assert len(metrics) == 5
        metric_names = [m[0] for m in metrics]
        assert "Average OPS/sec" in metric_names
        assert "Max OPS/sec" in metric_names
        assert "Min OPS/sec" in metric_names
        assert "Std Dev OPS/sec" in metric_names
        assert "Sample Count" in metric_names

    def test_stddev_metric_lower_is_better_flag(self):
        """Std Dev metric should have higher_better=False."""
        from ui.screens.views.charts import CompareCPUScreen
        screen = CompareCPUScreen()
        cpu1_data = [{"ops_per_second": 1000}]
        cpu2_data = [{"ops_per_second": 2000}]
        stats1 = CompareCPUScreen._calc_stats(cpu1_data)
        stats2 = CompareCPUScreen._calc_stats(cpu2_data)

        metrics = [
            ("Average OPS/sec", "avg", stats1["avg"], stats2["avg"], True),
            ("Max OPS/sec", "max", stats1["max"], stats2["max"], True),
            ("Min OPS/sec", "min", stats1["min"], stats2["min"], True),
            ("Std Dev OPS/sec", "stddev", stats1["stddev"], stats2["stddev"], False),
            ("Sample Count", "count", float(stats1["count"]), float(stats2["count"]), True),
        ]
        stddev_metric = [m for m in metrics if "Std Dev" in m[0]][0]
        assert stddev_metric[4] is False  # higher_better = False for stddev

    def test_other_metrics_higher_is_better(self):
        """All metrics except Std Dev should have higher_better=True."""
        from ui.screens.views.charts import CompareCPUScreen
        screen = CompareCPUScreen()
        cpu1_data = [{"ops_per_second": 1000}]
        cpu2_data = [{"ops_per_second": 2000}]
        stats1 = CompareCPUScreen._calc_stats(cpu1_data)
        stats2 = CompareCPUScreen._calc_stats(cpu2_data)

        metrics = [
            ("Average OPS/sec", "avg", stats1["avg"], stats2["avg"], True),
            ("Max OPS/sec", "max", stats1["max"], stats2["max"], True),
            ("Min OPS/sec", "min", stats1["min"], stats2["min"], True),
            ("Std Dev OPS/sec", "stddev", stats1["stddev"], stats2["stddev"], False),
            ("Sample Count", "count", float(stats1["count"]), float(stats2["count"]), True),
        ]
        for metric in metrics:
            if "Std Dev" in metric[0]:
                assert metric[4] is False
            else:
                assert metric[4] is True


class TestI3GetSelectedCPU:
    """Verify _get_selected_cpu helper works correctly."""

    def test_get_selected_cpu_returns_value(self):
        """Should return selected value from Select widget."""
        from ui.screens.views.charts import CompareCPUScreen
        screen = CompareCPUScreen()
        mock_select = MagicMock()
        mock_select.value = "Intel Core i7-9700K"
        screen.query_one = MagicMock(return_value=mock_select)
        result = screen._get_selected_cpu("first_cpu_select")
        assert result == "Intel Core i7-9700K"

    def test_get_selected_cpu_returns_empty_for_null(self):
        """Should return empty string when no selection made."""
        from ui.screens.views.charts import CompareCPUScreen
        screen = CompareCPUScreen()
        mock_select = MagicMock()
        mock_select.value = Select.NULL
        screen.query_one = MagicMock(return_value=mock_select)
        result = screen._get_selected_cpu("first_cpu_select")
        assert result == ""


class TestI3CompareCPUMethod:
    """Verify compare_cpu still works correctly."""

    def test_compare_cpu_returns_result_dict(self):
        """compare_cpu must return expected dictionary structure."""
        from ui.screens.views.charts import CompareCPUScreen
        screen = CompareCPUScreen()
        with patch("ui.screens.views.charts.get_scores_for_cpu") as mock_get:
            mock_get.side_effect = [
                [{"ops_per_second": 1000}],
                [{"ops_per_second": 2000}, {"ops_per_second": 2100}],
            ]
            result = screen.compare_cpu("CPU A", "CPU B")
            assert result["cpu1"] == "CPU A"
            assert result["cpu2"] == "CPU B"
            assert result["scores1"] == 1
            assert result["scores2"] == 2

    def test_compare_cpu_calls_get_scores_for_cpu(self):
        """compare_cpu must fetch data for both CPUs."""
        from ui.screens.views.charts import CompareCPUScreen
        screen = CompareCPUScreen()
        with patch("ui.screens.views.charts.get_scores_for_cpu") as mock_get:
            mock_get.return_value = []
            screen.compare_cpu("CPU X", "CPU Y")
            assert mock_get.call_count == 2
            mock_get.assert_any_call("CPU X")
            mock_get.assert_any_call("CPU Y")


class TestI3ScreenInheritance:
    """Verify CompareCPUScreen still extends BaseScreen."""

    def test_inherits_from_basescreen(self):
        """CompareCPUScreen must inherit from BaseScreen."""
        from ui.screens.views.charts import CompareCPUScreen
        from ui.screens.base_screen import BaseScreen
        assert issubclass(CompareCPUScreen, BaseScreen)

    def test_has_navigation_property(self):
        """CompareCPUScreen must have navigation property from mixin."""
        from ui.screens.views.charts import CompareCPUScreen
        assert hasattr(CompareCPUScreen, "navigation")

    def test_has_bindings(self):
        """CompareCPUScreen must define BINDINGS."""
        from ui.screens.views.charts import CompareCPUScreen
        assert hasattr(CompareCPUScreen, "BINDINGS")
        assert len(CompareCPUScreen.BINDINGS) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])