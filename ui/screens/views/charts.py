# ui/screens/views/charts.py: CompareCPUScreen
# Renders side-by-side CPU comparison tables with statistics.
# Provides comparison display components for textual-plotext integration.

from textual.widgets import (
    Static,
    Input,
    Button,
    DataTable,
)
from textual.containers import Container, Horizontal
from textual.binding import Binding
from textual.events import Key
import logging

from ui.shared import RETRO_GRADIENT_COLORS, colorize_text_gradient, WowFactorHeader

# Import core functions for data access and formatting
from core.benchmark import (
    get_scores_for_cpu,
    _get_all_valid_scores,
    format_large_number,
)

from ..base_screen import BaseScreen


class CompareCPUScreen(BaseScreen):
    """
    Screen for comparing two CPUs side-by-side.
    Features:
    - Dropdown selection for first CPU
    - Dropdown selection for second CPU
    - Side-by-side comparison display
    """

    BINDINGS = [
        ("b", "go_back", "Back to Main Menu"),
        ("q", "quit_app", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Container(classes="screen-container"):
            yield WowFactorHeader(id="app-header")
            yield Static(colorize_text_gradient("CPU COMPARISON", RETRO_GRADIENT_COLORS), classes="title")

            # CPU selection area
            with Horizontal(classes="cpu-selection"):
                yield Static("Select First CPU:", id="first_cpu_label", classes="form-label")
                yield Input(placeholder="Enter first CPU model...", id="first_cpu_input", classes="cpu-input form-input")

                yield Static("Select Second CPU:", id="second_cpu_label", classes="form-label")
                yield Input(placeholder="Enter second CPU model...", id="second_cpu_input", classes="cpu-input form-input")

            yield Button("Compare CPUs", id="compare_button", variant="primary", classes="action-btn")
            yield Static("Loading available CPUs...", id="loading_display")
            yield DataTable(id="comparison_table", classes="result-table")
            with Horizontal(classes="action-buttons"):
                yield Button("Back", id="back_to_main_menu", variant="default")

    def on_mount(self) -> None:
        self.query_one("#app-header", WowFactorHeader).update_title("CPU COMPARISON")
        self.available_cpus = []
        self.load_available_cpus()

    def load_available_cpus(self) -> None:
        """Load list of available CPU models from benchmark data."""
        try:
            scores = _get_all_valid_scores()
            # Extract unique CPU models
            cpu_models = set()
            for score in scores:
                model = score.get("processor_model", "")
                if model:
                    cpu_models.add(model)
            self.available_cpus = sorted(cpu_models)
            self.query_one("#loading_display", Static).display = False
        except Exception as e:
            self._show_error_message()

    def export_to_csv(self) -> None:
        """Export comparison data to CSV format (placeholder)."""
        # CompareCPUScreen doesn't have direct export functionality
        pass

    def compare_cpu(self, cpu1: str, cpu2: str) -> dict:
        """Compare two CPUs and return comparison results.

        Args:
            cpu1: First CPU model name.
            cpu2: Second CPU model name.

        Returns:
            Dictionary with CPU names and score counts.
        """
        scores1 = get_scores_for_cpu(cpu1)
        scores2 = get_scores_for_cpu(cpu2)

        result = {
            "cpu1": cpu1,
            "cpu2": cpu2,
            "scores1": len(scores1),
            "scores2": len(scores2),
        }
        return result

    def _show_error_message(self) -> None:
        """Show error message."""
        self.navigation.notify("Error loading CPUs.", type="error")

    def action_go_back(self) -> None:
        """Navigate back to main menu."""
        self.navigation.go_back()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "compare_button":
            first_cpu = self.query_one("#first_cpu_input", Input).value.strip()
            second_cpu = self.query_one("#second_cpu_input", Input).value.strip()

            if not first_cpu or not second_cpu:
                self.navigation.notify("Please enter both CPU models", type="warning")
                return

            # Load scores for each CPU and compare
            try:
                cpu1_data = get_scores_for_cpu(first_cpu)
                cpu2_data = get_scores_for_cpu(second_cpu)
                self.cpu1_data = cpu1_data
                self.cpu2_data = cpu2_data
                self._display_comparison()
            except Exception as e:
                self._show_error_message()
            event.stop()
        elif event.button.id == "back_to_main_menu":
            self.action_go_back()
            event.stop()
        elif event.button.id == "quit_app":
            self.app.exit()
            event.stop()

    def _update_comparison_table(self, cpu1_data: list, cpu2_data: list) -> None:
        """Update the comparison table with CPU data.

        Calculates and displays average, max, min OPS/sec and sample count
        for each CPU side by side.

        Args:
            cpu1_data: List of benchmark results for CPU 1.
            cpu2_data: List of benchmark results for CPU 2.
        """
        table = self.query_one("#comparison_table", DataTable)
        table.clear()

        # Add columns
        table.add_column("Metric", key="metric")
        table.add_column(cpu1_data[0].get("processor_model", "CPU 1") if cpu1_data else "CPU 1", key="cpu1")
        table.add_column(cpu2_data[0].get("processor_model", "CPU 2") if cpu2_data else "CPU 2", key="cpu2")

        # Calculate metrics
        def calc_stats(scores):
            if not scores:
                return {"avg": 0, "max": 0, "min": 0, "count": 0}
            ops = [s.get("ops_per_second", 0) for s in scores]
            return {
                "avg": sum(ops) / len(ops),
                "max": max(ops),
                "min": min(ops),
                "count": len(ops)
            }

        stats1 = calc_stats(cpu1_data)
        stats2 = calc_stats(cpu2_data)

        # Add rows
        table.add_row("Average OPS/sec", str(stats1["avg"]), str(stats2["avg"]))
        table.add_row("Max OPS/sec", str(stats1["max"]), str(stats2["max"]))
        table.add_row("Min OPS/sec", str(stats1["min"]), str(stats2["min"]))
        table.add_row("Sample Count", str(stats1["count"]), str(stats2["count"]))

    def _display_comparison(self) -> None:
        """Display the comparison results in a table.

        Shows Average OPS/sec, Max OPS/sec, and Number of Runs
        for each CPU in a formatted comparison table.
        """
        table = self.query_one("#comparison_table", DataTable)
        table.clear()

        # Add columns for comparison
        table.add_column("Metric", key="metric")
        table.add_column(self.query_one("#first_cpu_input", Input).value.strip(), key="cpu1")
        table.add_column(self.query_one("#second_cpu_input", Input).value.strip(), key="cpu2")

        # Calculate comparison metrics
        cpu1_data = getattr(self, 'cpu1_data', [])
        cpu2_data = getattr(self, 'cpu2_data', [])

        def avg_ops(data):
            if not data:
                return 0
            return sum(d.get("ops_per_second", 0) for d in data) / len(data)

        def max_ops(data):
            if not data:
                return 0
            return max(d.get("ops_per_second", 0) for d in data)

        metrics = [
            ("Average OPS/sec", avg_ops(cpu1_data), avg_ops(cpu2_data)),
            ("Max OPS/sec", max_ops(cpu1_data), max_ops(cpu2_data)),
            ("Number of Runs", len(cpu1_data), len(cpu2_data)),
        ]

        for metric, val1, val2 in metrics:
            table.add_row(metric, format_large_number(val1), format_large_number(val2))