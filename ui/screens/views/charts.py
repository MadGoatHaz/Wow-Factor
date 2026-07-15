# ui/screens/views/charts.py: CompareCPUScreen
# Renders side-by-side CPU comparison tables with statistics.
# Provides comparison display components for textual-plotext integration.

from __future__ import annotations

from math import sqrt

from textual.widgets import (
    Static,
    Button,
    DataTable,
    Select,
    Footer,
)
from textual.containers import Container, Horizontal
from textual.binding import Binding

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
    - Select dropdown for first CPU (populated from benchmark data)
    - Select dropdown for second CPU (populated from benchmark data)
    - Side-by-side comparison display with better/worse highlighting
    - Metrics: Average, Max, Min, Std Dev, Sample Count OPS/sec
    """

    BINDINGS = [
        Binding("b", "go_back", "Back"),
        Binding("q", "quit_app", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Container(classes="screen-container"):
            yield WowFactorHeader(id="app-header")
            yield Static(colorize_text_gradient("CPU COMPARISON", RETRO_GRADIENT_COLORS), classes="title")

            # CPU selection area
            with Horizontal(classes="cpu-selection"):
                yield Static("Select First CPU:", id="first_cpu_label", classes="form-label")
                yield Select(
                    [],
                    prompt="-- Select first CPU --",
                    allow_blank=True,
                    id="first_cpu_select",
                    classes="cpu-select form-input",
                )

                yield Static("Select Second CPU:", id="second_cpu_label", classes="form-label")
                yield Select(
                    [],
                    prompt="-- Select second CPU --",
                    allow_blank=True,
                    id="second_cpu_select",
                    classes="cpu-select form-input",
                )

            yield Button("Compare CPUs", id="compare_button", variant="primary", classes="action-btn")
            yield Static("Loading available CPUs...", id="loading_display")
            yield DataTable(id="comparison_table", classes="result-table")
            with Horizontal(classes="action-buttons"):
                yield Button("Back", id="back_to_main_menu", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#app-header", WowFactorHeader).update_title("CPU COMPARISON")
        self.available_cpus: list[str] = []
        self.cpu1_data: list[dict] = []
        self.cpu2_data: list[dict] = []
        self.load_available_cpus()

    def load_available_cpus(self) -> None:
        """Load list of available CPU models from benchmark data."""
        try:
            scores = _get_all_valid_scores()
            cpu_models: set[str] = set()
            for score in scores:
                model = score.get("processor_model", "")
                if model:
                    cpu_models.add(model)
            self.available_cpus = sorted(cpu_models)
            self._populate_select_widgets()
            self.query_one("#loading_display", Static).display = False
        except Exception as e:
            self._show_error_message()

    def _populate_select_widgets(self) -> None:
        """Populate both Select widgets with available CPU models."""
        options: list[tuple[str, str]] = [(model, model) for model in self.available_cpus]
        if not options:
            options = [("No CPUs available", "")]
        self.query_one("#first_cpu_select", Select).set_options(options)
        self.query_one("#second_cpu_select", Select).set_options(options)

    def export_to_csv(self) -> None:
        """Export comparison data to CSV format (placeholder)."""
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

    def _get_selected_cpu(self, select_id: str) -> str:
        """Get the currently selected CPU value from a Select widget."""
        select_widget = self.query_one(f"#{select_id}", Select)
        value = select_widget.value
        if value == Select.NULL:
            return ""
        return str(value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "compare_button":
            first_cpu = self._get_selected_cpu("first_cpu_select")
            second_cpu = self._get_selected_cpu("second_cpu_select")

            if not first_cpu or not second_cpu:
                self.navigation.notify("Please select both CPUs", type="warning")
                return

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

    @staticmethod
    def _calc_stats(scores: list[dict]) -> dict[str, float]:
        """Calculate statistical metrics from benchmark scores.

        Args:
            scores: List of benchmark score dictionaries with 'ops_per_second' key.

        Returns:
            Dictionary with avg, max, min, stddev, count metrics.
        """
        if not scores:
            return {"avg": 0, "max": 0, "min": 0, "stddev": 0, "count": 0}
        ops = [s.get("ops_per_second", 0) for s in scores]
        n = len(ops)
        avg = sum(ops) / n
        variance = sum((x - avg) ** 2 for x in ops) / n if n > 0 else 0
        stddev = sqrt(variance)
        return {
            "avg": avg,
            "max": max(ops),
            "min": min(ops),
            "stddev": stddev,
            "count": n,
        }

    def _display_comparison(self) -> None:
        """Display the comparison results in a table.

        Shows Average, Max, Min, Std Dev, and Sample Count OPS/sec
        for each CPU with better/worse visual differentiation.
        """
        table = self.query_one("#comparison_table", DataTable)
        table.clear()

        cpu1_name = self._get_selected_cpu("first_cpu_select")
        cpu2_name = self._get_selected_cpu("second_cpu_select")

        # Add columns for comparison
        table.add_column("Metric", key="metric")
        table.add_column(cpu1_name, key="cpu1")
        table.add_column(cpu2_name, key="cpu2")

        cpu1_data = getattr(self, "cpu1_data", [])
        cpu2_data = getattr(self, "cpu2_data", [])

        stats1 = self._calc_stats(cpu1_data)
        stats2 = self._calc_stats(cpu2_data)

        # Define metrics where higher is better
        higher_is_better = {"avg", "max", "min"}
        # For stddev, lower is better (more consistent)
        lower_is_better = {"stddev"}

        metrics: list[tuple[str, str, float, float, bool]] = [
            ("Average OPS/sec", "avg", stats1["avg"], stats2["avg"], True),
            ("Max OPS/sec", "max", stats1["max"], stats2["max"], True),
            ("Min OPS/sec", "min", stats1["min"], stats2["min"], True),
            ("Std Dev OPS/sec", "stddev", stats1["stddev"], stats2["stddev"], False),
            ("Sample Count", "count", float(stats1["count"]), float(stats2["count"]), True),
        ]

        for display_name, key, val1, val2, higher_better in metrics:
            # Determine which value is better
            if higher_better:
                better = 1 if val1 >= val2 else (2 if val2 > val1 else 0)
            else:
                better = 1 if val1 <= val2 else (2 if val2 < val1 else 0)

            cell1_value = format_large_number(val1)
            cell2_value = format_large_number(val2)

            # Apply Rich markup for better (green/bold) or worse (dim) values
            if better == 1:
                cell1_value = f"[bold green]{cell1_value}[/]"
                cell2_value = f"[dim]{cell2_value}[/]"
            elif better == 2:
                cell1_value = f"[dim]{cell1_value}[/]"
                cell2_value = f"[bold green]{cell2_value}[/]"

            table.add_row(display_name, cell1_value, cell2_value)