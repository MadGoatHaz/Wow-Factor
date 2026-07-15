"""Tests for CHUNK-I4: Fix Benchmark Progress Bars."""

import ast
import asyncio
import inspect
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure project root is on path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestI4SingleBenchmarkProgress:
    """Tests for RunSingleBenchmarkScreen progress bar improvements."""

    def test_progress_bar_not_fake_total(self):
        """Progress bar no longer uses total=999999999 fake value."""
        with open("ui/screens/benchmark.py") as f:
            source = f.read()
        assert "999999999" not in source, (
            "Fake total=999999999 should be removed from progress bars"
        )

    def test_no_loading_overlay_navigation(self):
        """Single benchmark should not navigate to loading overlay."""
        from ui.screens.benchmark import RunSingleBenchmarkScreen
        source = inspect.getsource(RunSingleBenchmarkScreen)
        assert 'navigate_to("loading_overlay")' not in source, (
            "Single benchmark should not push loading overlay"
        )
        assert 'navigate_to("loading_overlay"' not in source, (
            "No loading overlay navigation in single benchmark"
        )

    def test_no_markdown_widget_in_compose(self):
        """Single benchmark should not compose Markdown widget."""
        from ui.screens.benchmark import RunSingleBenchmarkScreen
        source = inspect.getsource(RunSingleBenchmarkScreen)
        assert "Markdown(" not in source, (
            "Markdown widget should be replaced by DataTable in single benchmark"
        )

    def test_datatable_in_compose(self):
        """Single benchmark should compose a DataTable for results."""
        from ui.screens.benchmark import RunSingleBenchmarkScreen
        source = inspect.getsource(RunSingleBenchmarkScreen)
        assert "DataTable" in source, (
            "DataTable should be composed for structured results display"
        )
        assert 'id="result_table"' in source, (
            "DataTable should have id='result_table'"
        )

    def test_progress_handler_uses_elapsed_time(self):
        """on_benchmark_progress should use elapsed_time for progress."""
        from ui.screens.benchmark import RunSingleBenchmarkScreen
        source = inspect.getsource(RunSingleBenchmarkScreen)
        assert "elapsed_time" in source or "_benchmark_duration" in source, (
            "Progress handler should use elapsed_time or duration for real progress"
        )

    def test_on_completion_no_overlay_dismissal(self):
        """on_benchmark_completion should not call go_back to dismiss overlay."""
        from ui.screens.benchmark import RunSingleBenchmarkScreen
        source = inspect.getsource(RunSingleBenchmarkScreen)
        method_source = source.split("def on_benchmark_completion")[1].split("def ")[0] if "def on_benchmark_completion" in source else ""
        assert "go_back" not in method_source, (
            "on_benchmark_completion should not call navigation.go_back() for overlay"
        )

    def test_no_json_dumps_in_single_screen(self):
        """Single benchmark should not dump raw JSON for results display."""
        from ui.screens.benchmark import RunSingleBenchmarkScreen
        source = inspect.getsource(RunSingleBenchmarkScreen)
        assert "json.dumps" not in source, (
            "Should not use json.dumps for results display"
        )

    def test_progress_bar_not_static_total(self):
        """Progress bar should not have hardcoded total=999999999."""
        from ui.screens.benchmark import RunSingleBenchmarkScreen
        source = inspect.getsource(RunSingleBenchmarkScreen)
        assert "total=999999999" not in source, (
            "ProgressBar should not use fake total value"
        )
        assert "elapsed_time" in source, (
            "Progress bar should use elapsed_time for real progress"
        )

    def test_duration_tracking_attribute(self):
        """Screen should track benchmark duration for progress calculation."""
        from ui.screens.benchmark import RunSingleBenchmarkScreen
        source = inspect.getsource(RunSingleBenchmarkScreen)
        assert "_benchmark_duration" in source, (
            "Screen should track _benchmark_duration for time-based progress"
        )


class TestI4BatchBenchmarkProgress:
    """Tests for RunBatchBenchmarkScreen progress bar improvements."""

    def test_progress_bar_uses_batch_count(self):
        """Batch progress bar should use actual batch run count as total."""
        from ui.screens.benchmark import RunBatchBenchmarkScreen
        source = inspect.getsource(RunBatchBenchmarkScreen)
        assert "total_runs" in source or "_total_batch_runs" in source, (
            "Batch progress should use real batch run count"
        )

    def test_no_markdown_widget_in_batch_compose(self):
        """Batch benchmark should not compose Markdown widget."""
        from ui.screens.benchmark import RunBatchBenchmarkScreen
        source = inspect.getsource(RunBatchBenchmarkScreen)
        assert "Markdown(" not in source, (
            "Markdown widget should be replaced by DataTable in batch benchmark"
        )

    def test_datatable_in_batch_compose(self):
        """Batch benchmark should compose a DataTable for results."""
        from ui.screens.benchmark import RunBatchBenchmarkScreen
        source = inspect.getsource(RunBatchBenchmarkScreen)
        assert "DataTable" in source, (
            "DataTable should be composed for structured batch results"
        )
        assert 'id="batch_result_table"' in source, (
            "DataTable should have id='batch_result_table'"
        )

    def test_batch_progress_shows_run_number(self):
        """Batch progress handler should update with batch_run_number."""
        from ui.screens.benchmark import RunBatchBenchmarkScreen
        source = inspect.getsource(RunBatchBenchmarkScreen)
        assert "batch_run_number" in source, (
            "Batch progress should display run number in progress bar"
        )

    def test_no_json_dumps_in_batch_screen(self):
        """Batch benchmark should not dump raw JSON for results display."""
        from ui.screens.benchmark import RunBatchBenchmarkScreen
        source = inspect.getsource(RunBatchBenchmarkScreen)
        assert "json.dumps" not in source, (
            "Should not use json.dumps for batch results display"
        )

    def test_batch_result_table_display(self):
        """Batch completion should populate DataTable with per-run data."""
        from ui.screens.benchmark import RunBatchBenchmarkScreen
        source = inspect.getsource(RunBatchBenchmarkScreen)
        assert "batch_result_table" in source, (
            "Batch results should be displayed in batch_result_table DataTable"
        )


class TestI4AsyncCooldown:
    """Tests for async sleep replacement in batch cooldown."""

    def test_no_time_sleep_in_batch_worker(self):
        """Batch worker should not use time.sleep (blocks event loop)."""
        from ui.screens.benchmark import RunBatchBenchmarkScreen
        worker_source = inspect.getsource(
            RunBatchBenchmarkScreen._batch_benchmark_worker_function
        )
        assert "time.sleep" not in worker_source, (
            "Batch worker cooldown should use asyncio.sleep, not time.sleep"
        )

    def test_uses_asyncio_sleep_in_cooldown(self):
        """Batch worker cooldown should use await asyncio.sleep."""
        from ui.screens.benchmark import RunBatchBenchmarkScreen
        worker_source = inspect.getsource(
            RunBatchBenchmarkScreen._batch_benchmark_worker_function
        )
        assert "asyncio.sleep" in worker_source, (
            "Batch worker cooldown should use await asyncio.sleep(1)"
        )

    def test_batch_worker_is_async(self):
        """_batch_benchmark_worker_function should be an async function."""
        from ui.screens.benchmark import RunBatchBenchmarkScreen
        func = RunBatchBenchmarkScreen._batch_benchmark_worker_function
        assert asyncio.iscoroutinefunction(func), (
            "_batch_benchmark_worker_function should be async to use asyncio.sleep"
        )


class TestI4BenchmarkProgressMessage:
    """Tests for BenchmarkProgress message with elapsed_time."""

    def test_message_has_elapsed_time_field(self):
        """BenchmarkProgress message should include elapsed_time."""
        from ui.messages import BenchmarkProgress
        msg = BenchmarkProgress(total_ops=1000, ops_per_second=500.0, elapsed_time=2.0)
        assert msg.elapsed_time == 2.0
        assert msg.total_ops == 1000
        assert msg.ops_per_second == 500.0

    def test_message_elapsed_time_defaults_to_zero(self):
        """BenchmarkProgress elapsed_time should default to 0.0."""
        from ui.messages import BenchmarkProgress
        msg = BenchmarkProgress(total_ops=100, ops_per_second=10.0)
        assert msg.elapsed_time == 0.0


class TestI4ModuleLevelChecks:
    """Module-level checks for I4 changes."""

    def test_no_markdown_import_in_benchmark_module(self):
        """benchmark.py should not import Markdown widget."""
        with open("ui/screens/benchmark.py") as f:
            source = f.read()
        widgets_line = [l for l in source.split("\n") if "from textual.widgets" in l][0]
        assert "Markdown" not in widgets_line, (
            "Markdown import should be removed from benchmark.py"
        )

    def test_datatable_import_in_benchmark_module(self):
        """benchmark.py should import DataTable widget."""
        with open("ui/screens/benchmark.py") as f:
            source = f.read()
        widgets_line = [l for l in source.split("\n") if "from textual.widgets" in l][0]
        assert "DataTable" in widgets_line, (
            "DataTable should be imported in benchmark.py"
        )

    def test_asyncio_import_in_benchmark_module(self):
        """benchmark.py should import asyncio for non-blocking sleep."""
        with open("ui/screens/benchmark.py") as f:
            source = f.read()
        assert "import asyncio" in source, (
            "asyncio should be imported for await asyncio.sleep()"
        )

    def test_no_time_sleep_in_benchmark_module(self):
        """benchmark.py should not contain time.sleep anywhere."""
        with open("ui/screens/benchmark.py") as f:
            source = f.read()
        assert "time.sleep" not in source, (
            "All time.sleep calls should be replaced with asyncio.sleep"
        )

    def test_no_navigate_to_loading_overlay_in_module(self):
        """benchmark.py should not navigate to loading overlay anywhere."""
        with open("ui/screens/benchmark.py") as f:
            source = f.read()
        assert 'loading_overlay' not in source, (
            "loading_overlay navigation should be removed from benchmark.py"
        )

    def test_benchmark_module_imports_cleanly(self):
        """benchmark.py should import without errors."""
        try:
            from ui.screens.benchmark import (
                RunSingleBenchmarkScreen,
                RunBatchBenchmarkScreen,
            )
            assert RunSingleBenchmarkScreen is not None
            assert RunBatchBenchmarkScreen is not None
        except ImportError as e:
            pytest.fail(f"Failed to import benchmark screens: {e}")