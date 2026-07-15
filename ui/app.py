"""Main application module for WowFactor TUI."""

import datetime
import logging
from typing import List, Dict

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Static, Button

# Import theme system and layout utilities
from ui.theme import ColorPalette, SpacingScale
from ui.layout_utils import LayoutOptimizer, DataTableLayoutManager

from ui.shared import RETRO_GRADIENT_COLORS, colorize_text_gradient, WowFactorHeader
from ui.screens.main_menu import MainMenuScreen
from ui.screens.benchmark import RunSingleBenchmarkScreen, RunBatchBenchmarkScreen
from ui.screens.views import ViewBestScoresScreen, CompareCPUScreen, ViewAllScoresScreen
from ui.screens.analytics import AnalyticsScreen, TrendsChartScreen
from ui.screens.cleanup import ClearInvalidScoresResultScreen
from ui.screens.overlay import LoadingOverlay
from ui.screens.confirmation import ClearInvalidScoresConfirmationScreen
from ui.screens.profile_selection import ProfileSelectionScreen
from ui.screens.profile_creation import ProfileCreationScreen
from ui.navigation import NavigationManager


class DataExportMixin:
    """Mixin to provide CSV, JSON, XML, and YAML export functionality to Screens."""

    def export_data(self, data: List[Dict], table, export_type: str, filename_prefix: str) -> None:
        """
        Main entry point for exporting data.
        
        Args:
            data: List of dictionaries (source of truth for JSON).
            table: DataTable instance (source of truth for CSV columns).
            export_type: 'csv', 'json', 'xml', or 'yaml'.
            filename_prefix: Prefix for the output filename.
        """
        if not data and (not table or not table.rows):
             if self.query("DataTable"): # Check if table exists in hierarchy
                self.query_one("#loading_display", Static).update("[yellow]No data to export.[/yellow]")
                self.query_one("#loading_display", Static).display = True
             return

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.{export_type}"
        
        try:
            if export_type == 'csv':
                self._write_csv(table, filename)
            elif export_type == 'json':
                self._write_json(data, filename)
            elif export_type == 'xml':
                from core.exporters import XmlExporter
                XmlExporter.export(data, filename)
            elif export_type == 'yaml':
                from core.exporters import YamlExporter
                YamlExporter.export(data, filename)
            else:
                logging.error(f"Unknown export type: {export_type}")
                return

            self.query_one("#loading_display", Static).update(f"[green]Exported to {filename}[/green]")
            self.query_one("#loading_display", Static).display = True

        except PermissionError as e:
            self.query_one("#loading_display", Static).update(f"[red]Permission denied: {filename}[/red]")
            self.query_one("#loading_display", Static).display = True
            logging.error(f"Permission error during export: {e}")
        except OSError as e:
            self.query_one("#loading_display", Static).update(f"[red]OS error: {str(e)}[/red]")
            self.query_one("#loading_display", Static).display = True
            logging.error(f"OS error during export: {e}")
        except Exception as e:
            self.query_one("#loading_display", Static).update(f"[red]Export failed: {str(e)}[/red]")
            self.query_one("#loading_display", Static).display = True
            logging.error(f"Export failed: {e}")

    def _write_csv(self, table, filename: str) -> None:
        import csv
        import re
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header row based on table column labels
            headers = [str(col.label) for col in table.columns.values()]
            writer.writerow(headers)
            
            # Write data rows
            for row in table.rows:
                row_values = []
                for key in table.columns.keys():
                    cell_value = table.get_cell(row, key)
                    # Strip Textual markup (e.g. [bold]text[/]) using regex
                    clean_value = re.sub(r'\[.*?\]', '', str(cell_value))
                    row_values.append(clean_value)
                writer.writerow(row_values)

    def _write_json(self, data: List[Dict], filename: str) -> None:
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def _write_xml(self, data: List[Dict], filename: str) -> None:
        from core.exporters import XmlExporter
        XmlExporter.export(data, filename)

    def _write_yaml(self, data: List[Dict], filename: str) -> None:
        from core.exporters import YamlExporter
        YamlExporter.export(data, filename)


class WowFactorTUI(App):
    """Main TUI application for WowFactor."""
    
    SCREENS = {
        "main_menu": MainMenuScreen,
        "run_single_benchmark": RunSingleBenchmarkScreen,
        "run_batch_benchmark": RunBatchBenchmarkScreen,
        "view_best_scores": ViewBestScoresScreen,
        "compare_cpu": CompareCPUScreen,
        "view_all_scores": ViewAllScoresScreen,
        "clear_invalid_confirm": ClearInvalidScoresConfirmationScreen,
        "clear_invalid_result": ClearInvalidScoresResultScreen,
        "profile_selection": ProfileSelectionScreen,
        "profile_creation": ProfileCreationScreen,
        "analytics": AnalyticsScreen,
        "trends_chart": TrendsChartScreen,
        "loading_overlay": LoadingOverlay,
    }
    
    CSS_PATH = "styles.tcss"  # Load theme stylesheet
    
    def __init__(self) -> None:
        super().__init__()
        self.navigation = NavigationManager()
        # Initialize layout manager for optimized column width calculations
        self.layout_manager = DataTableLayoutManager()
    
    def on_mount(self) -> None:
        self.navigation.initialize(self)
        self.push_screen("main_menu")
