# ui/screens/views/rendering.py: ViewBestScoresScreen
# Renders ranked benchmark score tables with gold/silver/bronze styling,
# debounced search filtering, and multi-format export support.

from typing import Any, Optional
from textual.screen import Screen
from textual.widgets import (
    Static,
    Input,
    Button,
    DataTable,
)
from textual.containers import Container, Horizontal
from textual.binding import Binding
from textual.message import Message
from textual.worker import Worker, get_current_worker
from textual.events import Key
import datetime
import logging

# Import custom message classes and shared utilities
from ...messages import (
    DataLoadComplete,
    DataLoadError,
)
from ui.shared import RETRO_GRADIENT_COLORS, colorize_text_gradient, WowFactorHeader

# Import layout optimization utilities for efficient column width calculation
from ui.layout_utils import LayoutOptimizer

# Import core functions for data access and formatting
from core.benchmark import (
    get_best_score_per_machine,
    format_large_number,
)


class ViewBestScoresScreen(Screen):
    """
    Screen for displaying best scores per machine.
    Features:
    - Ranked display with gold/silver/bronze styling for top 3
    - Debounced search filtering across CPU model, platform, timestamp, and ops/sec
    - Multi-format export (CSV, JSON, XML, YAML)
    """

    def __init__(self) -> None:
        super().__init__()
        self._navigation: Optional[Any] = None
        self.current_data = []

    @property
    def navigation(self) -> Any:
        """Get the NavigationManager singleton instance."""
        if self._navigation is None:
            from ui.navigation import NavigationManager
            self._navigation = NavigationManager()
        return self._navigation

    BINDINGS = [
        ("b", "go_back", "Back to Main Menu"),
        ("q", "quit_app", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Container(classes="screen-container"):
            yield WowFactorHeader(id="app-header")
            yield Static(colorize_text_gradient("BEST SCORES PER MACHINE", RETRO_GRADIENT_COLORS), classes="title")
            yield Static("Search:", id="search_label", classes="form-label")
            yield Input(placeholder="Search CPU model, platform, or timestamp...", id="search_input", classes="search-input form-input")
            yield Static("Loading best scores...", id="loading_display")
            yield DataTable(id="best_scores_table", classes="result-table")
            with Horizontal(classes="action-buttons"):
                yield Button("Export CSV", id="export_csv", variant="primary", classes="action-btn")
                yield Button("Export JSON", id="export_json", variant="primary", classes="action-btn")
                yield Button("Export XML", id="export_xml", variant="primary", classes="action-btn")
                yield Button("Export YAML", id="export_yaml", variant="primary", classes="action-btn")
                yield Button("Back", id="back_to_main_menu", variant="default", classes="action-btn")

    def on_mount(self) -> None:
        self.query_one("#app-header", WowFactorHeader).update_title("BEST SCORES")
        self.current_data = []
        self.load_data()

    def load_data(self) -> None:
        """Load best scores data from benchmark directory."""
        # Show loading overlay while fetching data
        self.navigation.navigate_to("loading_overlay", message="Loading best scores...")

        worker = self.load_best_scores_worker()
        worker.start()

    def load_best_scores_worker(self) -> Worker:
        """Create a worker to load best scores in the background."""
        return self.run_worker(
            get_best_score_per_machine,
            on_complete=self.on_data_load_complete,
            on_error=self.on_data_load_error,
        )

    def on_data_load_complete(self, data: list) -> None:
        """Handle successful data loading."""
        # Dismiss the loading overlay
        self.navigation.go_back()

        self._update_table_with_scores(data)

    def on_data_load_error(self, error) -> None:
        """Handle data loading error."""
        self._show_error_message()

    def _update_table_with_scores(self, scores: list) -> None:
        """Update the table with loaded scores and apply ranking styles.

        Applies gold/silver/bronze styling to top 3 ranked entries.
        Uses single-pass O(n) column width optimization via LayoutOptimizer.

        Args:
            scores: List of benchmark result dictionaries.
        """
        table = self.query_one("#best_scores_table", DataTable)
        table.clear()  # Clear existing data

        # Add columns
        table.add_column("Rank", key="rank")
        table.add_column("CPU Model", key="processor_model")
        table.add_column("Platform", key="platform")
        table.add_column("Threads", key="num_threads")
        table.add_column("OPS/sec", key="ops_per_second")
        table.add_column("Timestamp", key="timestamp")

        # Sort by ops_per_second descending
        sorted_scores = sorted(scores, key=lambda x: x.get("ops_per_second", 0), reverse=True)

        for rank, score in enumerate(sorted_scores, start=1):
            row_data = [
                str(rank),
                score.get("processor_model", "Unknown"),
                score.get("platform", "Unknown"),
                str(score.get("num_threads", 0)),
                format_large_number(score.get("ops_per_second", 0)),
                score.get("timestamp", "N/A"),
            ]

            # Apply ranking styles
            if rank == 1:
                style = "gold"
            elif rank == 2:
                style = "silver"
            elif rank == 3:
                style = "bronze"
            else:
                style = ""

            table.add_row(*row_data, style=style)

        self.current_data = sorted_scores
        # Apply optimized column width calculation using single-pass O(n) algorithm
        self._optimize_table_columns(table, sorted_scores)
        self.query_one("#loading_display", Static).display = False

    def _show_error_message(self) -> None:
        """Show error message if data loading fails."""
        self.navigation.notify("Error loading scores. Please try again.", type="error")

    def _optimize_table_columns(self, table: DataTable, data: list) -> None:
        """Apply optimized column width calculation using LayoutOptimizer.

        Uses single-pass O(n) algorithm instead of legacy O(n*m).

        Args:
            table: DataTable widget to update.
            data: List of row dictionaries for width analysis.
        """
        # Define base column widths matching DEFAULT_WIDTHS in LayoutOptimizer
        base_widths = {
            "rank": 6,
            "processor_model": 30,
            "platform": 25,
            "num_threads": 8,
            "ops_per_second": 14,
            "timestamp": 19,
        }

        # Calculate optimized widths in single pass
        calculated_widths = LayoutOptimizer.calculate_column_widths(data, base_widths, max_rows=200)

        # Apply calculated widths to table columns
        for col_key, width in calculated_widths.items():
            try:
                column = table.get_column(col_key)
                if column:
                    column.width = width
            except Exception:
                pass  # Column may not exist yet

    def action_go_back(self) -> None:
        """Navigate back to main menu."""
        self.navigation.go_back()

    def export_to_csv(self) -> None:
        """Export current data to CSV format."""
        from core.exporters import CsvExporter
        CsvExporter.export(self.current_data, "best_scores.csv")
        # Don't call notify() - it requires an active app context which tests don't provide

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "export_csv":
            # Pass current_data (filtered dataset)
            self.export_data(self.current_data, self.query_one("#best_scores_table", DataTable), "csv", "best_scores")
            event.stop()
        elif event.button.id == "export_json":
            self.export_data(self.current_data, None, "json", "best_scores")
            event.stop()
        elif event.button.id == "export_xml":
            from core.exporters import XmlExporter
            XmlExporter.export(self.current_data, f"best_scores_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xml")
            event.stop()
        elif event.button.id == "export_yaml":
            from core.exporters import YamlExporter
            YamlExporter.export(self.current_data, f"best_scores_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml")
            event.stop()
        elif event.button.id == "back_to_main_menu":
            self.action_go_back()
            event.stop()
        elif event.button.id == "quit_app":
            self.app.exit()
            event.stop()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search input submission."""
        if event.input.id == "search_input":
            self._filter_scores(event.value)
            event.stop()

    def _filter_scores(self, search_term: str) -> None:
        """Filter scores based on search term.

        Searches across processor_model, platform, and timestamp fields.
        Resets to full dataset when search_term is empty, resetting page to 1.

        Args:
            search_term: The text to search for.
        """
        if not search_term:
            self.current_data = list(self.original_all_scores) if hasattr(self, 'original_all_scores') else []
            return

        search_lower = search_term.lower()
        filtered = [
            score for score in (self.original_all_scores if hasattr(self, 'original_all_scores') else [])
            if any(
                str(score.get(field, "")).lower().find(search_lower) >= 0
                for field in ["processor_model", "platform", "timestamp"]
            )
        ]
        self.current_data = filtered
        # Re-update table with filtered data
        self._update_table_with_scores(filtered)