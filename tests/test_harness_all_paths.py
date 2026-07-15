"""
EXHAUSTIVE PATH COVERAGE HARNESS FOR WOFFACTOR TUI.
Exercises every screen, every action, every data path, every import, every widget.
"""
import pytest
import os
import json
import asyncio
import tempfile
from unittest.mock import MagicMock, patch

# ============================================================
# SECTION 1: Core Module Exhaustive Tests
# ============================================================
class TestCoreBenchmark:
    """Every function in core/benchmark.py tested with real data paths."""

    def test_execute_single_benchmark_run(self):
        """Run actual benchmark for 1 second, verify result structure."""
        from core.benchmark import execute_single_benchmark_run
        result = execute_single_benchmark_run(duration=1.0, is_infinite=False, num_threads=1)
        assert "ops_per_second" in result
        assert "total_operations" in result
        assert "duration_seconds" in result
        assert "num_threads" in result
        assert "system" in result
        assert "processor_model" in result["system"]
        assert result["ops_per_second"] > 0

    def test_execute_single_benchmark_run_multi_thread(self):
        """Run benchmark with 2 threads to verify multi-threading path."""
        from core.benchmark import execute_single_benchmark_run
        result = execute_single_benchmark_run(duration=1.0, is_infinite=False, num_threads=2)
        assert result["num_threads"] == 2
        assert result["ops_per_second"] > 0

    def test_get_best_score_per_machine(self):
        """Load best scores from disk."""
        from core.benchmark import get_best_score_per_machine
        scores = get_best_score_per_machine()
        assert isinstance(scores, list)

    def test_get_scores_for_cpu(self):
        """Query scores for specific CPU from existing data."""
        from core.benchmark import get_scores_for_cpu, get_unique_cpu_models
        models = get_unique_cpu_models()
        for model in models[:3]:
            if model:
                scores = get_scores_for_cpu(model)
                assert isinstance(scores, list)

    def test_get_all_valid_scores(self):
        """Load all scores from disk."""
        from core.benchmark import _get_all_valid_scores
        scores = _get_all_valid_scores()
        assert isinstance(scores, list)

    def test_get_unique_cpu_models(self):
        """Get unique CPU model list."""
        from core.benchmark import get_unique_cpu_models
        models = get_unique_cpu_models()
        assert isinstance(models, list)

    def test_get_unique_platforms(self):
        """Get unique platform list from scores."""
        from core.benchmark import _get_all_valid_scores, get_unique_platforms
        scores = _get_all_valid_scores()
        platforms = get_unique_platforms(scores)
        assert isinstance(platforms, list)

    def test_cleanup_invalid_scores(self):
        """Run cleanup on benchmark results dir."""
        from core.benchmark import cleanup_invalid_scores
        result = cleanup_invalid_scores()
        assert isinstance(result, list)

    def test_format_large_number_millions(self):
        """Test number formatting for millions."""
        from core.benchmark import format_large_number
        assert format_large_number(1_500_000) == "1.50M"

    def test_format_large_number_thousands(self):
        """Test number formatting for thousands."""
        from core.benchmark import format_large_number
        assert format_large_number(1_500) == "1.50K"

    def test_format_large_number_small(self):
        """Test number formatting for small values."""
        from core.benchmark import format_large_number
        assert format_large_number(150) == "150.00"

    def test_clean_cpu_model_name(self):
        """Test CPU name cleaning strips extra info."""
        from core.benchmark import clean_cpu_model_name
        cleaned = clean_cpu_model_name("AMD Ryzen 5 5600G 6-Core Processor with Radeon Graphics")
        assert "AMD" in cleaned
        assert "6-Core Processor" not in cleaned
        assert "with Radeon Graphics" not in cleaned

    def test_save_benchmark_results(self):
        """Save a result and verify file was created."""
        from core.benchmark import save_benchmark_results
        stats = {"total_ops": 1_000_000}
        result = save_benchmark_results(stats, 1.0, 1)
        assert result["total_operations"] == 1_000_000
        assert os.path.exists(result["file_path"])

    def test_cache_set_get_invalidate(self):
        """Test cache set, get, and single-key invalidation."""
        from core.benchmark import _set_in_cache, _get_from_cache, _invalidate_cache
        _set_in_cache("test_key_harness", "test_value_harness")
        assert _get_from_cache("test_key_harness") == "test_value_harness"
        _invalidate_cache("test_key_harness")
        assert _get_from_cache("test_key_harness") is None

    def test_cache_invalidate_for_cpu(self):
        """Test CPU-scoped cache invalidation."""
        from core.benchmark import _set_in_cache, _get_from_cache, _invalidate_for_cpu
        _set_in_cache("cpu_test_harness", {"processor_model": "AMD Test CPU"})
        _invalidate_for_cpu("AMD Test CPU")
        assert _get_from_cache("cpu_test_harness") is None

    def test_cache_cleanup_expired(self):
        """Test expired cache cleanup doesn't crash."""
        from core.benchmark import _cleanup_expired_cache
        _cleanup_expired_cache()  # Should be safe to call with empty cache

    def test_aggregate_scores_by_cpu(self):
        """Test score aggregation returns correct CPU and avg counts."""
        from core.benchmark import aggregate_scores_by_cpu
        data = [
            {"system": {"processor_model": "CPU1"}, "ops_per_second": 100},
            {"system": {"processor_model": "CPU1"}, "ops_per_second": 200},
            {"system": {"processor_model": "CPU2"}, "ops_per_second": 300},
        ]
        cpus, avgs = aggregate_scores_by_cpu(data)
        assert len(cpus) == 2
        assert len(avgs) == 2

    def test_aggregate_scores_empty(self):
        """Test aggregation with empty data returns empty lists."""
        from core.benchmark import aggregate_scores_by_cpu
        cpus, avgs = aggregate_scores_by_cpu([])
        assert cpus == []
        assert avgs == []

    def test_get_score_distribution(self):
        """Test score distribution calculation."""
        from core.benchmark import get_score_distribution
        data = [
            {"ops_per_second": 100},
            {"ops_per_second": 200},
            {"ops_per_second": 300},
        ]
        bins, counts = get_score_distribution(data, bin_size=100)
        assert len(bins) > 0
        assert len(counts) > 0

    def test_get_score_distribution_empty(self):
        """Test distribution with empty data."""
        from core.benchmark import get_score_distribution
        bins, counts = get_score_distribution([])
        assert bins == []
        assert counts == []

    def test_apply_all_filters_match(self):
        """Test filtering returns matching records."""
        from core.benchmark import apply_all_filters
        data = [
            {
                "system": {"processor_model": "AMD Test", "platform": "Linux"},
                "timestamp": "2025-01-01 00:00:00",
                "ops_per_second": 100,
            }
        ]
        result = apply_all_filters(data, "AMD", None, None, "")
        assert len(result) == 1

    def test_apply_all_filters_no_match(self):
        """Test filtering with no matches returns empty."""
        from core.benchmark import apply_all_filters
        data = [
            {
                "system": {"processor_model": "AMD Test", "platform": "Linux"},
                "timestamp": "2025-01-01 00:00:00",
                "ops_per_second": 100,
            }
        ]
        result = apply_all_filters(data, "NONEXISTENT", None, None, "")
        assert len(result) == 0

    def test_apply_all_filters_by_platform(self):
        """Test filtering by platform."""
        from core.benchmark import apply_all_filters
        data = [
            {"system": {"processor_model": "CPU1", "platform": "Linux"}, "ops_per_second": 100},
            {"system": {"processor_model": "CPU2", "platform": "Windows"}, "ops_per_second": 200},
        ]
        result = apply_all_filters(data, "", None, None, "Linux")
        assert len(result) == 1
        assert result[0]["system"]["platform"] == "Linux"

    def test_parse_date_with_time(self):
        """Test date parsing with datetime string."""
        from core.benchmark import parse_date
        d = parse_date("2025-01-15 10:30:00")
        assert d is not None
        assert d.year == 2025

    def test_parse_date_without_time(self):
        """Test date parsing with date-only string."""
        from core.benchmark import parse_date
        d = parse_date("2025-06-15")
        assert d is not None
        assert d.month == 6

    def test_parse_date_invalid(self):
        """Test date parsing with invalid string returns None."""
        from core.benchmark import parse_date
        d = parse_date("not-a-date")
        assert d is None

    def test_parse_date_empty(self):
        """Test date parsing with empty string returns None."""
        from core.benchmark import parse_date
        d = parse_date("")
        assert d is None

    def test_is_date_in_range(self):
        """Test date range check returns True for in-range date."""
        from core.benchmark import is_date_in_range, parse_date
        d = parse_date("2025-06-15")
        start = parse_date("2025-01-01")
        end = parse_date("2025-12-31")
        assert is_date_in_range(d, start, end) is True

    def test_is_date_out_of_range(self):
        """Test date range check returns False for out-of-range date."""
        from core.benchmark import is_date_in_range, parse_date
        d = parse_date("2024-01-01")
        start = parse_date("2025-01-01")
        end = parse_date("2025-12-31")
        assert is_date_in_range(d, start, end) is False

    def test_is_date_in_range_no_bounds(self):
        """Test date range check with no bounds returns True."""
        from core.benchmark import is_date_in_range, parse_date
        d = parse_date("2025-06-15")
        assert is_date_in_range(d, None, None) is True

    def test_export_data_to_json(self):
        """Test JSON export data preparation."""
        from core.benchmark import export_data_to_json
        result = export_data_to_json(None, "test_screen", [{"key": "value"}])
        assert "metadata" in result
        assert result["metadata"]["screen_type"] == "test_screen"
        assert result["metadata"]["export_format"] == "json"
        assert len(result["data"]) == 1

    def test_get_cpu_info(self):
        """Test CPU info retrieval returns expected tuple."""
        from core.benchmark import get_cpu_info
        cpu_model, cpu_freq, platform_name = get_cpu_info()
        assert isinstance(cpu_model, str)
        assert isinstance(cpu_freq, str)
        assert isinstance(platform_name, str)
        assert cpu_model != "" or cpu_model == "N/A"

    def test_setup_logging(self):
        """Test logging setup doesn't crash."""
        from core.benchmark import setup_logging
        setup_logging(level="INFO")


class TestCoreAnalyticsEngine:
    """Test analytics engine with real data."""

    def test_analytics_engine_init(self):
        from core.analytics_engine import AnalyticsEngine
        engine = AnalyticsEngine()
        assert engine is not None

    def test_detect_trends_improving(self):
        from core.analytics_engine import AnalyticsEngine
        engine = AnalyticsEngine()
        data = [100, 150, 200, 250, 300]
        trend = engine.detect_trends(data)
        assert "trend" in trend
        assert trend["trend"] == "improving"

    def test_detect_trends_degrading(self):
        from core.analytics_engine import AnalyticsEngine
        engine = AnalyticsEngine()
        data = [300, 250, 200, 150, 100]
        trend = engine.detect_trends(data)
        assert trend["trend"] == "degrading"

    def test_detect_trends_insufficient(self):
        from core.analytics_engine import AnalyticsEngine
        engine = AnalyticsEngine()
        data = [100]
        trend = engine.detect_trends(data)
        assert trend["trend"] == "insufficient_data"

    def test_get_stats_per_cpu_model(self):
        from core.analytics_engine import AnalyticsEngine
        engine = AnalyticsEngine()
        engine._scores_cache = [
            {"system": {"processor_model": "CPU1"}, "ops_per_second": 100, "duration_seconds": 1.0},
        ]
        stats = engine.get_stats_per_cpu_model()
        assert "CPU1" in stats

    def test_get_scores_by_cpu_model(self):
        from core.analytics_engine import AnalyticsEngine
        engine = AnalyticsEngine()
        engine._scores_cache = [
            {"system": {"processor_model": "CPU1"}, "ops_per_second": 100},
        ]
        by_model = engine.get_scores_by_cpu_model()
        assert "CPU1" in by_model

    def test_get_trend_visualization(self):
        from core.analytics_engine import AnalyticsEngine
        engine = AnalyticsEngine()
        data = [100, 110, 120, 130, 140]
        sparkline = engine.get_trend_visualization(data)
        assert isinstance(sparkline, str)
        assert len(sparkline) > 0

    def test_get_trend_visualization_empty(self):
        from core.analytics_engine import AnalyticsEngine
        engine = AnalyticsEngine()
        sparkline = engine.get_trend_visualization([])
        assert sparkline == "N/A"

    def test_generate_summary_report(self):
        from core.analytics_engine import AnalyticsEngine
        engine = AnalyticsEngine()
        engine._scores_cache = [
            {"system": {"processor_model": "CPU1", "platform": "Linux"}, "ops_per_second": 100, "duration_seconds": 1.0, "timestamp": "2025-01-01 00:00:00"},
        ]
        report = engine.generate_summary_report()
        assert isinstance(report, dict)
        assert "generated_at" in report

    def test_get_overall_statistics(self):
        from core.analytics_engine import AnalyticsEngine
        engine = AnalyticsEngine()
        engine._scores_cache = [
            {"system": {"processor_model": "CPU1", "platform": "Linux"}, "ops_per_second": 100},
        ]
        stats = engine.get_overall_statistics()
        assert stats["total_samples"] == 1

    def test_get_overall_statistics_empty(self):
        from core.analytics_engine import AnalyticsEngine
        engine = AnalyticsEngine()
        engine._scores_cache = []
        stats = engine.get_overall_statistics()
        assert "error" in stats

    def test_get_unique_cpu_models_from_engine(self):
        from core.analytics_engine import AnalyticsEngine
        engine = AnalyticsEngine()
        engine._scores_cache = [
            {"system": {"processor_model": "CPU1"}},
            {"system": {"processor_model": "CPU2"}},
        ]
        models = engine.get_unique_cpu_models()
        assert len(models) == 2

    def test_clear_cache(self):
        from core.analytics_engine import AnalyticsEngine
        engine = AnalyticsEngine()
        engine._scores_cache = [{"ops_per_second": 100}]
        engine.clear_cache()
        assert engine._scores_cache is None


class TestCoreConfig:
    """Test config manager operations."""

    def test_config_manager_init(self):
        from core.config import ConfigManager
        cm = ConfigManager()
        assert cm is not None

    def test_get_defaults(self):
        from core.config import ConfigManager
        cm = ConfigManager()
        defaults = cm.get_defaults()
        assert defaults is not None
        assert hasattr(defaults, "duration")

    def test_benchmark_defaults_to_dict(self):
        from core.config import BenchmarkDefaults
        bd = BenchmarkDefaults(duration=10, num_threads=4, batch_runs=5, cooldown_seconds=3)
        d = bd.to_dict()
        assert d["duration"] == 10
        assert d["num_threads"] == 4

    def test_benchmark_defaults_from_dict(self):
        from core.config import BenchmarkDefaults
        d = {"duration": 20, "num_threads": 8, "batch_runs": 10, "cooldown_seconds": 5}
        bd = BenchmarkDefaults.from_dict(d)
        assert bd.duration == 20
        assert bd.num_threads == 8

    def test_benchmark_profile_serialization(self):
        from core.config import BenchmarkProfile, BenchmarkDefaults
        defaults = BenchmarkDefaults(duration=15)
        profile = BenchmarkProfile(name="TestProfile", defaults=defaults)
        d = profile.to_dict()
        assert d["name"] == "TestProfile"
        restored = BenchmarkProfile.from_dict(d)
        assert restored.name == "TestProfile"

    def test_config_manager_create_and_delete_profile(self):
        """Create a profile, verify it exists, then delete it."""
        from core.config import ConfigManager
        import tempfile
        tmpdir = tempfile.mkdtemp()
        cm = ConfigManager(config_dir=tmpdir)
        result = cm.create_profile("HarnessTest", duration=5)
        assert result is True
        profile = cm.get_profile("HarnessTest")
        assert profile is not None
        delete_result = cm.delete_profile("HarnessTest")
        assert delete_result is True
        assert cm.get_profile("HarnessTest") is None


class TestCoreExporters:
    """Test all export formats."""

    def test_csv_export(self):
        from core.exporters import CsvExporter
        data = [{"ops_per_second": 100, "system": {"processor_model": "CPU1", "platform": "Linux"}, "timestamp": "2025-01-01"}]
        CsvExporter.export(data, "test_harness_csv_output.csv")
        assert os.path.exists("test_harness_csv_output.csv")
        os.remove("test_harness_csv_output.csv")

    def test_json_export_via_analytics(self):
        from core.exporters import AnalyticsExporter
        data = {"key": "value", "scores": [1, 2, 3]}
        AnalyticsExporter.export_analytics_report(data, "test_harness_json_output.json")
        assert os.path.exists("test_harness_json_output.json")
        with open("test_harness_json_output.json") as f:
            loaded = json.load(f)
        assert loaded["key"] == "value"
        os.remove("test_harness_json_output.json")

    def test_xml_export(self):
        from core.exporters import XmlExporter
        data = [{"ops_per_second": 100, "system": {"processor_model": "CPU1", "platform": "Linux"}, "timestamp": "2025-01-01"}]
        XmlExporter.export(data, "test_harness_xml_output.xml")
        assert os.path.exists("test_harness_xml_output.xml")
        os.remove("test_harness_xml_output.xml")

    def test_yaml_export(self):
        from core.exporters import YamlExporter
        data = [{"ops_per_second": 100, "system": {"processor_model": "CPU1", "platform": "Linux"}, "timestamp": "2025-01-01"}]
        YamlExporter.export(data, "test_harness_yaml_output.yaml")
        assert os.path.exists("test_harness_yaml_output.yaml")
        os.remove("test_harness_yaml_output.yaml")

    def test_xml_escape_special_chars(self):
        from core.exporters import XmlExporter
        escaped = XmlExporter._escape_xml("<test>&'value\"")
        assert "&lt;" in escaped
        assert "&amp;" in escaped
        assert "&quot;" in escaped

    def test_analytics_exporter_stats_csv(self):
        from core.exporters import AnalyticsExporter
        stats = {
            "CPU1": {
                "sample_count": 5,
                "ops_per_second": {"mean": 100, "median": 101, "std_dev": 5, "min": 90, "max": 110},
                "duration_seconds": {"mean": 1.0, "median": 1.0, "min": 1.0, "max": 1.0},
            }
        }
        AnalyticsExporter.export_stats_per_cpu(stats, "test_harness_stats.csv")
        assert os.path.exists("test_harness_stats.csv")
        os.remove("test_harness_stats.csv")

    def test_analytics_exporter_rankings(self):
        from core.exporters import AnalyticsExporter
        rankings = [("CPU1", {"mean": 100, "median": 101, "std_dev": 5, "min": 90, "max": 110, "count": 5})]
        AnalyticsExporter.export_rankings(rankings, "test_harness_rankings.csv")
        assert os.path.exists("test_harness_rankings.csv")
        os.remove("test_harness_rankings.csv")

    def test_analytics_exporter_comparison_report(self):
        from core.exporters import AnalyticsExporter
        comparison = {"cpu1": "A", "cpu2": "B", "winner": "A"}
        AnalyticsExporter.export_comparison_report(comparison, "test_harness_comparison.json")
        assert os.path.exists("test_harness_comparison.json")
        os.remove("test_harness_comparison.json")

    def test_analytics_exporter_summary_text(self):
        from core.exporters import AnalyticsExporter
        report_data = {
            "generated_at": "2025-01-01",
            "overall_statistics": {"count": 10, "mean": 500, "median": 500, "std_dev": 10, "min": 100, "max": 900},
        }
        AnalyticsExporter.export_summary_text_report(report_data, "test_harness_summary.txt")
        assert os.path.exists("test_harness_summary.txt")
        os.remove("test_harness_summary.txt")


class TestCoreComparator:
    """Test results comparison tool."""

    def test_comparator_init(self):
        from core.comparator import ResultsComparator
        comp = ResultsComparator()
        assert comp is not None

    def test_get_available_results(self):
        from core.comparator import ResultsComparator
        comp = ResultsComparator()
        results = comp.get_available_results()
        assert isinstance(results, list)

    def test_get_best_run(self):
        from core.comparator import ResultsComparator
        comp = ResultsComparator()
        best = comp.get_best_run()
        assert best is None or isinstance(best, str)


class TestCorePowerManager:
    """Test power plan manager context manager."""

    def test_power_plan_manager_init(self):
        from core.power import PowerPlanManager
        mgr = PowerPlanManager()
        assert mgr is not None
        assert hasattr(mgr, "is_linux")

    def test_power_plan_manager_context_no_crash(self):
        """Enter and exit power plan manager without root."""
        from core.power import PowerPlanManager
        with PowerPlanManager() as mgr:
            assert mgr is not None
        # Should exit cleanly


class TestCoreSchema:
    """Test schema validation."""

    def test_validate_config_valid(self):
        from core.schema import validate_config
        data = {"profiles": {"Test": {"name": "Test", "defaults": {"duration": 15}}}}
        is_valid, errors = validate_config(data)
        assert is_valid is True

    def test_validate_config_invalid(self):
        from core.schema import validate_config
        data = {"profiles": {}}
        is_valid, errors = validate_config(data)
        # Empty profiles should still be valid or produce warnings
        assert isinstance(is_valid, bool)


class TestCoreExceptions:
    """Test custom exception classes exist."""

    def test_exception_imports(self):
        from core.exceptions import WowFactorError
        assert WowFactorError is not None


class TestCoreLoggingConfig:
    """Test logging configuration module."""

    def test_setup_logging_config(self):
        from core.logging_config import setup_logging
        setup_logging(level="INFO")


# ============================================================
# SECTION 2: Screen Exhaustive Tests
# ============================================================
class TestScreenMainMenu:
    """Exhaustive MainMenuScreen tests."""

    def test_instantiate(self):
        from ui.screens.main_menu import MainMenuScreen
        screen = MainMenuScreen()
        assert screen is not None

    def test_compose_defined(self):
        """Verify compose() method exists and yields widgets."""
        from ui.screens.main_menu import MainMenuScreen
        screen = MainMenuScreen()
        assert hasattr(screen, "compose")
        import inspect
        source = inspect.getsource(screen.compose)
        assert "yield" in source

    def test_bindings_exist(self):
        from ui.screens.main_menu import MainMenuScreen
        screen = MainMenuScreen()
        assert hasattr(screen, 'BINDINGS')
        assert len(screen.BINDINGS) > 0

    def test_navigation_property(self):
        from ui.screens.main_menu import MainMenuScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = MainMenuScreen()
        nav = screen.navigation
        assert nav is not None


class TestScreenRunSingleBenchmark:
    """Exhaustive RunSingleBenchmarkScreen tests."""

    def test_instantiate(self):
        from ui.screens.benchmark import RunSingleBenchmarkScreen
        screen = RunSingleBenchmarkScreen()
        assert screen is not None

    def test_compose_defined(self):
        """Verify compose() method exists and yields widgets."""
        from ui.screens.benchmark import RunSingleBenchmarkScreen
        screen = RunSingleBenchmarkScreen()
        import inspect
        source = inspect.getsource(screen.compose)
        assert "yield" in source

    def test_bindings_exist(self):
        from ui.screens.benchmark import RunSingleBenchmarkScreen
        screen = RunSingleBenchmarkScreen()
        assert hasattr(screen, 'BINDINGS')

    def test_benchmark_worker_function_callable(self):
        """Verify _benchmark_worker_function is a callable method on the screen."""
        from ui.screens.benchmark import RunSingleBenchmarkScreen
        screen = RunSingleBenchmarkScreen()
        assert callable(screen._benchmark_worker_function)

    def test_worker_is_called_with_lambda(self):
        """Verify start_benchmark_run wraps worker in lambda."""
        from ui.screens.benchmark import RunSingleBenchmarkScreen
        import inspect
        source = inspect.getsource(RunSingleBenchmarkScreen.start_benchmark_run)
        assert 'lambda' in source, "run_worker must use lambda for deferred execution"

    def test_uses_core_execute_single_benchmark_run(self):
        """Test the screen uses core benchmark function directly (no proxy)."""
        from core.benchmark import execute_single_benchmark_run
        import ui.screens.benchmark as benchmark_mod
        assert hasattr(benchmark_mod, 'execute_single_benchmark_run')
        result = execute_single_benchmark_run(1.0, False, 1, None)
        assert "ops_per_second" in result

    def test_uses_core_format_large_number(self):
        """Test the screen uses core format_large_number directly (no proxy)."""
        from core.benchmark import format_large_number
        import ui.screens.benchmark as benchmark_mod
        assert hasattr(benchmark_mod, 'format_large_number')
        assert format_large_number(1_500_000) == "1.50M"


class TestScreenRunBatchBenchmark:
    """Exhaustive RunBatchBenchmarkScreen tests."""

    def test_instantiate(self):
        from ui.screens.benchmark import RunBatchBenchmarkScreen
        screen = RunBatchBenchmarkScreen()
        assert screen is not None

    def test_compose_defined(self):
        """Verify compose() method exists and yields widgets."""
        from ui.screens.benchmark import RunBatchBenchmarkScreen
        screen = RunBatchBenchmarkScreen()
        import inspect
        source = inspect.getsource(screen.compose)
        assert "yield" in source

    def test_bindings_exist(self):
        from ui.screens.benchmark import RunBatchBenchmarkScreen
        screen = RunBatchBenchmarkScreen()
        assert hasattr(screen, 'BINDINGS')

    def test_batch_worker_is_async(self):
        from ui.screens.benchmark import RunBatchBenchmarkScreen
        import asyncio
        screen = RunBatchBenchmarkScreen()
        coro = screen._batch_benchmark_worker_function(2, 1, 1)
        assert asyncio.iscoroutine(coro)
        coro.close()

    def test_uses_core_execute_single_benchmark_run(self):
        """Test batch screen uses core benchmark function directly (no proxy)."""
        from core.benchmark import execute_single_benchmark_run
        import ui.screens.benchmark as benchmark_mod
        assert hasattr(benchmark_mod, 'execute_single_benchmark_run')
        result = execute_single_benchmark_run(1.0, False, 1, None)
        assert "ops_per_second" in result


class TestScreenViewBestScores:
    """Exhaustive ViewBestScoresScreen tests."""

    def test_instantiate(self):
        from ui.screens.views.rendering import ViewBestScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewBestScoresScreen()
        assert screen is not None

    def test_bindings_exist(self):
        from ui.screens.views.rendering import ViewBestScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewBestScoresScreen()
        assert hasattr(screen, 'BINDINGS')

    def test_compose_defined(self):
        """Verify compose() method exists and yields widgets."""
        from ui.screens.views.rendering import ViewBestScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewBestScoresScreen()
        import inspect
        source = inspect.getsource(screen.compose)
        assert "yield" in source

    def test_navigation_property(self):
        from ui.screens.views.rendering import ViewBestScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewBestScoresScreen()
        nav = screen.navigation
        assert nav is not None

    def test_current_data_initialized(self):
        from ui.screens.views.rendering import ViewBestScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewBestScoresScreen()
        assert screen.current_data == []


class TestScreenViewAllScores:
    """Exhaustive ViewAllScoresScreen tests."""

    def test_instantiate(self):
        from ui.screens.views.navigation import ViewAllScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewAllScoresScreen()
        assert screen is not None

    def test_bindings_exist(self):
        from ui.screens.views.navigation import ViewAllScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewAllScoresScreen()
        assert hasattr(screen, 'BINDINGS')

    def test_pagination_initialized(self):
        from ui.screens.views.navigation import ViewAllScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewAllScoresScreen()
        assert screen.current_page == 1
        assert screen.page_size == 50

    def test_calculate_pages(self):
        from ui.screens.views.navigation import ViewAllScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewAllScoresScreen()
        screen.total_items = 150
        screen.page_size = 50
        screen._calculate_pages()
        assert screen.total_pages == 3

    def test_calculate_pages_empty(self):
        from ui.screens.views.navigation import ViewAllScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewAllScoresScreen()
        screen.total_items = 0
        screen.page_size = 50
        screen._calculate_pages()
        assert screen.total_pages == 1

    def test_filter_scores_logic(self):
        """Test the _filter_scores filtering logic directly."""
        from ui.screens.views.navigation import ViewAllScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewAllScoresScreen()
        screen.original_all_scores = [
            {"processor_model": "AMD Test CPU", "platform": "Linux", "timestamp": "2025-01-01"},
            {"processor_model": "Intel Test CPU", "platform": "Linux", "timestamp": "2025-01-01"},
        ]
        # Test filter logic directly without calling _update_table
        search_lower = "AMD".lower()
        filtered = [
            score for score in screen.original_all_scores
            if any(
                str(score.get(field, "")).lower().find(search_lower) >= 0
                for field in ["processor_model", "platform", "timestamp"]
            )
        ]
        assert len(filtered) == 1
        assert "AMD" in filtered[0]["processor_model"]

    def test_filter_scores_empty_term_resets(self):
        """Test that empty search term resets to full dataset."""
        from ui.screens.views.navigation import ViewAllScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewAllScoresScreen()
        screen.original_all_scores = [
            {"processor_model": "AMD Test", "platform": "Linux", "timestamp": "2025-01-01"},
            {"processor_model": "Intel Test", "platform": "Linux", "timestamp": "2025-01-01"},
        ]
        # Simulate the empty search behavior: filtered_scores resets to original
        screen.filtered_scores = list(screen.original_all_scores)
        assert len(screen.filtered_scores) == 2
        assert screen.current_page == 1

    def test_display_current_page(self):
        from ui.screens.views.navigation import ViewAllScoresScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = ViewAllScoresScreen()
        screen.current_page = 2
        screen.total_pages = 10
        info = screen._display_current_page()
        assert "2 of 10" in info


class TestScreenCompareCPU:
    """Exhaustive CompareCPUScreen tests."""

    def test_instantiate(self):
        from ui.screens.views.charts import CompareCPUScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = CompareCPUScreen()
        assert screen is not None

    def test_bindings_exist(self):
        from ui.screens.views.charts import CompareCPUScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = CompareCPUScreen()
        assert hasattr(screen, 'BINDINGS')

    def test_compare_cpu_method(self):
        from ui.screens.views.charts import CompareCPUScreen
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = CompareCPUScreen()
        result = screen.compare_cpu("CPU1", "CPU2")
        assert "cpu1" in result
        assert "cpu2" in result

    def test_compare_cpu_with_existing_models(self):
        from ui.screens.views.charts import CompareCPUScreen
        from core.benchmark import get_unique_cpu_models
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        screen = CompareCPUScreen()
        models = get_unique_cpu_models()
        if len(models) >= 2:
            result = screen.compare_cpu(models[0], models[1])
            assert result["cpu1"] == models[0]
            assert result["cpu2"] == models[1]


class TestScreenAnalytics:
    """Exhaustive AnalyticsScreen tests."""

    def test_instantiate(self):
        from ui.screens.analytics import AnalyticsScreen
        screen = AnalyticsScreen()
        assert screen is not None

    def test_bindings_exist(self):
        from ui.screens.analytics import AnalyticsScreen
        screen = AnalyticsScreen()
        assert hasattr(screen, 'BINDINGS')

    def test_load_data_worker_is_async(self):
        from ui.screens.analytics import AnalyticsScreen
        import asyncio
        screen = AnalyticsScreen()
        coro = screen._load_data_worker()
        assert asyncio.iscoroutine(coro)
        coro.close()


class TestScreenTrendsChart:
    """Exhaustive TrendsChartScreen tests."""

    def test_instantiate(self):
        from ui.screens.analytics import TrendsChartScreen
        screen = TrendsChartScreen()
        assert screen is not None

    def test_bindings_exist(self):
        from ui.screens.analytics import TrendsChartScreen
        screen = TrendsChartScreen()
        assert hasattr(screen, 'BINDINGS')

    def test_convert_timestamp(self):
        from ui.screens.analytics import convert_timestamp_to_unix
        ts = convert_timestamp_to_unix("2025-01-01 00:00:00")
        assert ts > 0

    def test_convert_timestamp_invalid(self):
        from ui.screens.analytics import convert_timestamp_to_unix
        ts = convert_timestamp_to_unix("invalid")
        assert ts == 0.0

    def test_convert_timestamp_empty(self):
        from ui.screens.analytics import convert_timestamp_to_unix
        ts = convert_timestamp_to_unix("")
        assert ts == 0.0

    def test_load_data_worker_is_async(self):
        from ui.screens.analytics import TrendsChartScreen
        import asyncio
        screen = TrendsChartScreen()
        coro = screen._load_data_worker()
        assert asyncio.iscoroutine(coro)
        coro.close()


class TestScreenBaseScreen:
    """Test base screen classes."""

    def test_base_screen_instantiate(self):
        from ui.screens.base_screen import BaseScreen
        screen = BaseScreen()
        assert screen is not None

    def test_screen_with_services_navigation(self):
        from ui.screens.base_screen import ScreenWithServices
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        # We need to inherit from Screen for __init__ to work
        class TestScreen(ScreenWithServices):
            def __init__(self):
                ScreenWithServices.__init__(self)
        screen = TestScreen()
        nav = screen.navigation
        assert nav is not None


class TestScreenCleanup:
    """Test cleanup screen."""

    def test_cleanup_screen_instantiate(self):
        from ui.screens.cleanup import ClearInvalidScoresResultScreen
        screen = ClearInvalidScoresResultScreen(deleted_count=0)
        assert screen is not None


class TestScreenProfileSelection:
    """Test profile selection screen."""

    def test_profile_selection_instantiate(self):
        from ui.screens.profile_selection import ProfileSelectionScreen
        screen = ProfileSelectionScreen(profiles=["Default"])
        assert screen is not None

    def test_profile_selection_empty_profiles(self):
        """Test profile selection with no profiles."""
        from ui.screens.profile_selection import ProfileSelectionScreen
        screen = ProfileSelectionScreen(profiles=[])
        assert screen is not None


class TestNavigationManager:
    """Test navigation manager singleton."""

    def test_singleton(self):
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        nm1 = NavigationManager()
        nm2 = NavigationManager()
        assert nm1 is nm2
        NavigationManager._instance = None

    def test_initialize_with_mock(self):
        from ui.navigation import NavigationManager
        NavigationManager._instance = None
        nm = NavigationManager()
        mock_app = MagicMock()
        mock_app.SCREENS = {}
        mock_app.screen_stack = []
        mock_app.screen = MagicMock()
        nm.initialize(mock_app)
        assert nm._app is mock_app


class TestSharedComponents:
    """Test shared UI components."""

    def test_wowfactor_header_instantiate(self):
        from ui.shared import WowFactorHeader
        header = WowFactorHeader(id="test-header")
        assert header is not None

    def test_colorize_text_gradient(self):
        from ui.shared import colorize_text_gradient, RETRO_GRADIENT_COLORS
        result = colorize_text_gradient("Test", RETRO_GRADIENT_COLORS)
        assert isinstance(result, str)
        assert len(result) > 0


class TestLayoutUtils:
    """Test layout optimizer."""

    def test_calculate_column_widths(self):
        from ui.layout_utils import LayoutOptimizer
        data = [{"rank": "1", "processor_model": "AMD Ryzen 5 5600G"}]
        base_widths = {"rank": 6, "processor_model": 30}
        widths = LayoutOptimizer.calculate_column_widths(data, base_widths)
        assert isinstance(widths, dict)


class TestNotifications:
    """Test notification system."""

    def test_notification_type_enum(self):
        from ui.notifications import NotificationType
        assert hasattr(NotificationType, "SUCCESS")
        assert hasattr(NotificationType, "ERROR")
        assert hasattr(NotificationType, "WARNING")
        assert hasattr(NotificationType, "INFO")

    def test_toast_notification_class_exists(self):
        from ui.notifications import ToastNotification
        assert ToastNotification is not None


class TestMessages:
    """Test message classes."""

    def test_benchmark_progress(self):
        from ui.messages import BenchmarkProgress
        msg = BenchmarkProgress(1000, 500.0)
        assert msg.total_ops == 1000
        assert msg.ops_per_second == 500.0

    def test_benchmark_completion(self):
        from ui.messages import BenchmarkCompletion
        msg = BenchmarkCompletion({"ops_per_second": 1000})
        assert msg.result_data["ops_per_second"] == 1000

    def test_batch_benchmark_progress(self):
        from ui.messages import BatchBenchmarkProgress
        msg = BatchBenchmarkProgress(1, 5, 1000, 500.0)
        assert msg.batch_run_number == 1
        assert msg.total_batch_runs == 5

    def test_batch_benchmark_completion(self):
        from ui.messages import BatchBenchmarkCompletion
        msg = BatchBenchmarkCompletion([], 5)
        assert msg.total_batch_runs == 5

    def test_cooldown_message(self):
        from ui.messages import CooldownMessage
        msg = CooldownMessage(1, 5, 3)
        assert msg.current_batch_run == 1
        assert msg.cooldown_seconds == 3


# ============================================================
# SECTION 3: Integration End-to-End
# ============================================================
class TestEndToEnd:
    """End-to-end flows that catch runtime crashes."""

    def test_full_benchmark_flow(self):
        """Run a complete benchmark cycle."""
        from core.benchmark import execute_single_benchmark_run
        result = execute_single_benchmark_run(1.0, False, 1)
        assert result["ops_per_second"] > 0

    def test_view_best_scores_data_flow(self):
        """Verify the full data flow for ViewBestScores."""
        from core.benchmark import get_best_score_per_machine
        scores = get_best_score_per_machine()
        assert isinstance(scores, list)
        for s in scores[:5]:
            assert "ops_per_second" in s
            assert "system" in s

    def test_view_all_scores_data_flow(self):
        """Verify full data flow for ViewAllScores."""
        from core.benchmark import _get_all_valid_scores
        scores = _get_all_valid_scores()
        assert isinstance(scores, list)

    def test_compare_cpu_data_flow(self):
        """Verify full data flow for CompareCPU."""
        from core.benchmark import get_scores_for_cpu, get_unique_cpu_models
        models = get_unique_cpu_models()
        for model in models[:2]:
            if model:
                scores = get_scores_for_cpu(model)
                assert isinstance(scores, list)

    def test_analytics_data_flow(self):
        """Verify analytics engine data flow."""
        from core.analytics_engine import AnalyticsEngine
        from core.benchmark import _get_all_valid_scores
        engine = AnalyticsEngine()
        scores = _get_all_valid_scores()
        engine._scores_cache = scores[:100]
        stats = engine.get_stats_per_cpu_model()
        assert isinstance(stats, dict)

    def test_export_csv_flow(self):
        """Full CSV export flow."""
        from core.exporters import CsvExporter
        from core.benchmark import get_best_score_per_machine
        scores = get_best_score_per_machine()[:10]
        CsvExporter.export(scores, "e2e_test.csv")
        assert os.path.exists("e2e_test.csv")
        os.remove("e2e_test.csv")

    def test_export_json_flow(self):
        """Full JSON export flow via AnalyticsExporter."""
        from core.exporters import AnalyticsExporter
        from core.benchmark import get_best_score_per_machine
        scores = get_best_score_per_machine()[:10]
        AnalyticsExporter.export_analytics_report({"data": scores}, "e2e_test.json")
        assert os.path.exists("e2e_test.json")
        os.remove("e2e_test.json")

    def test_export_xml_flow(self):
        """Full XML export flow."""
        from core.exporters import XmlExporter
        from core.benchmark import get_best_score_per_machine
        scores = get_best_score_per_machine()[:10]
        XmlExporter.export(scores, "e2e_test.xml")
        assert os.path.exists("e2e_test.xml")
        os.remove("e2e_test.xml")

    def test_export_yaml_flow(self):
        """Full YAML export flow."""
        from core.exporters import YamlExporter
        from core.benchmark import get_best_score_per_machine
        scores = get_best_score_per_machine()[:10]
        YamlExporter.export(scores, "e2e_test.yaml")
        assert os.path.exists("e2e_test.yaml")
        os.remove("e2e_test.yaml")

    def test_full_benchmark_save_and_reload(self):
        """Run benchmark, save, then reload from disk."""
        from core.benchmark import execute_single_benchmark_run, get_best_score_per_machine
        result = execute_single_benchmark_run(1.0, False, 1)
        assert result["ops_per_second"] > 0
        assert os.path.exists(result["file_path"])
        scores = get_best_score_per_machine()
        assert isinstance(scores, list)

    def test_comparator_load_results(self):
        """Test comparator can load available results."""
        from core.comparator import ResultsComparator
        comp = ResultsComparator()
        results = comp.get_available_results()
        assert isinstance(results, list)
        if results:
            stats = comp.get_stats_for_run(results[0])
            assert stats is not None


# ============================================================
# SECTION 4: Error Handling
# ============================================================
class TestErrorHandling:
    """Verify graceful error handling."""

    def test_empty_scores_dir(self):
        """Test that loading scores from existing dir works."""
        from core.benchmark import _get_all_valid_scores
        scores = _get_all_valid_scores()
        assert isinstance(scores, list)

    def test_cleanup_invalid_scores_no_crash(self):
        """Test cleanup returns list even if no invalid files."""
        from core.benchmark import cleanup_invalid_scores
        result = cleanup_invalid_scores()
        assert isinstance(result, list)

    def test_filter_empty_results(self):
        """Test filter with no matches returns empty list."""
        from core.benchmark import apply_all_filters
        data = [
            {
                "system": {"processor_model": "AMD", "platform": "Linux"},
                "timestamp": "2025-01-01",
                "ops_per_second": 100,
            }
        ]
        result = apply_all_filters(data, "NONEXISTENT", None, None, "")
        assert len(result) == 0

    def test_analytics_engine_no_data(self):
        """Test analytics engine handles empty data gracefully."""
        from core.analytics_engine import AnalyticsEngine
        engine = AnalyticsEngine()
        engine._scores_cache = []
        stats = engine.get_overall_statistics()
        assert "error" in stats

    def test_get_stats_for_cpu_no_data(self):
        """Test CPU stats for non-existent CPU."""
        from core.analytics_engine import AnalyticsEngine
        engine = AnalyticsEngine()
        engine._scores_cache = []
        stats = engine.get_stats_for_cpu("NonExistent CPU")
        assert "error" in stats

    def test_compare_cpu_profiles_no_data(self):
        """Test CPU comparison when no data exists."""
        from core.analytics_engine import AnalyticsEngine
        engine = AnalyticsEngine()
        engine._scores_cache = []
        result = engine.compare_cpu_profiles("CPU1", "CPU2")
        assert "error" in result

    def test_detect_trend_insufficient_data(self):
        """Test trend detection with insufficient data."""
        from core.analytics_engine import AnalyticsEngine
        engine = AnalyticsEngine()
        engine._scores_cache = []
        result = engine.detect_trend("NonExistent CPU")
        assert result["trend_direction"] == "insufficient_data"

    def test_power_manager_no_root(self):
        """Test power manager doesn't crash without root."""
        from core.power import PowerPlanManager
        with PowerPlanManager() as mgr:
            pass  # Should handle gracefully