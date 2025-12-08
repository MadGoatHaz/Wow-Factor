#!/usr/bin/env python3

"""
UI Components Module for WowFactor TUI Application.
This module contains all UI components extracted from wow.py
"""

from typing import List, Dict, Any
import time
import json
import logging
import multiprocessing
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static, Input, DataTable, Markdown, TabbedContent, TabPane
from textual.containers import Container, VerticalScroll, Horizontal
from textual.screen import Screen
from textual_plotext import PlotextPlot
from textual.worker import Worker
from textual.message import Message

# Import custom message classes
from ui.messages import (
    BenchmarkProgress,
    BenchmarkCompletion,
    BatchBenchmarkProgress,
    BatchBenchmarkCompletion,
    CooldownMessage,
    DataLoadComplete,
    DataLoadError
)

# Import all necessary core functions and constants from wow_core.py, but not UI-specific ones
from core.benchmark import (
    setup_logging, get_cpu_info, execute_single_benchmark_run,
    _get_all_valid_scores, get_best_score_per_machine, get_scores_for_cpu,
    get_unique_cpu_models, cleanup_invalid_scores, format_large_number,
    aggregate_scores_by_cpu, get_score_distribution,
    LOG_DIR, BENCHMARK_DIR, LOG_FILE # Import constants from core as well
)


# Add these methods to the Screen classes
# This is a workaround to make core functions available as methods on screens
# We'll add them to each screen class manually below

# --- NEW ASCII ART (Defined directly in wow.py as it's a UI asset) ---
WOW_FACTOR_ASCII_ART = r"""
 __      __               ___________              __
/  \    /  \______  _  __ \_   _____/____    _____/  |_  ___________
\   \/\/   /  _ \ \/ \/ /  |    __) \__  \ _/ ___\   __\/  _ \_  __ \
 \        (  <_> )     /   |     \   / __ \\  \___|  | (  <_> )  | \/
  \__/\  / \____/ \/\_/    \___  /  (____  /\___  >__|  \____/|__|
       \/                      \/        \/     \/
"""

# --- Gradient and Color Definitions (Defined directly in wow.py as they are UI assets) ---
RETRO_GRADIENT_COLORS = [
    "#FF00FF", "#FF33FF", "#00FFFF",
    "#33FFFF", "#00FF00", "#33FF33",
    "#FFFF00", "#FFFF33", "#FF0000",
    "#FF3300"
]

# Simple colorize function for Textual's rich content
def colorize_text_gradient(text: str, colors: List[str]) -> str:
    if not colors:
        return text
    num_colors = len(colors)
    colored_chars = []
    for i, char in enumerate(text):
        if char.isspace():
            colored_chars.append(char)
        else:
            color = colors[i % num_colors]
            colored_chars.append(f"[{color}]{char}[/]")
    return "".join(colored_chars)

# --- Textual CSS Styling ---
CLI_STYLESHEET = """
Screen {
    background: #000022; /* Dark blue/purple background */
    color: #00FFFF; /* Cyan default text */
}
Header {
    text-align: center;
    color: #FF00FF; /* Magenta */
    background: #440044; /* Darker Magenta */
    height: 3;
    content-align: center middle;
}
Container, VerticalScroll {
    margin: 0;
    padding: 0;
}
Header .subtitle {
    color: #00FFFF; /* Cyan */
}
Footer {
    background: #440044; /* Darker Magenta */
    color: #00FFFF; /* Cyan */
}
Button {
    background: #000088; /* Dark Blue */
    color: #00FFFF; /* Cyan */
    border: thick #FF00FF; /* Magenta border */
    width: 60%;
    /* Removed margin property, relying on parent container's align */
}
Button:hover {
    background: #0000FF; /* Brighter Blue */
    color: #FFFF00; /* Yellow */
}
.main-menu-container {
    align: center middle;
}
.menu-buttons {
    align: center middle; /* Center the buttons within this scrollable area */
}
.metric-name {
    color: #FFFF00; /* Yellow for metric names */
}
.metric-value {
    color: #00FF00; /* Green for metric values */
}
.gold-rank {
    color: #FFD700; /* Gold */
}
.silver-rank {
    color: #C0C0C0; /* Silver */
}
.bronze-rank {
    color: #CD7F32; /* Bronze */
}
.neon-green-rank {
    color: #39FF14; /* Neon Green */
}
.dark-blue-rank {
    color: #AAAAFF; /* Light Blue for general text, adapting from original dark blue */
}
.run-benchmark-screen {
    align: center top;
}

.run-benchmark-screen Input {
    width: 30;
    margin: 1 0;
    text-align: center;
    background: #000088;
    color: #00FFFF;
    border: thick #FF00FF;
}

.run-benchmark-screen #progress-display {
    width: 60%;
    height: 5;
    background: #220022;
    color: #00FF00;
    border: tall #00FFFF;
    margin: 1 0;
    text-align: center;
    overflow: hidden scroll;
}

.result-summary {
    width: 80%;
    margin: 1 0;
    background: #110011;
    border: solid #FF00FF;
    padding: 1;
}

.result-table {
    width: 80%;
    height: auto;
    max-height: 15;
    margin: 1 0;
}
.search-input {
    width: 60%;
    margin: 1 0;
    text-align: center;
    background: #000088;
    color: #00FFFF;
    border: thick #FF00FF;
}

.pagination-controls {
    width: 100%;
    height: auto;
    margin: 1 0;
    align: center middle;
}

.pagination-info {
    width: 100%;
    text-align: center;
    color: #00FFFF;
    margin: 1 0;
}

.pagination-buttons {
    width: 100%;
    height: auto;
    align: center middle;
    margin: 0;
}

.pagination-buttons Button {
    width: 14%;
    margin: 0 1;
}

.export-buttons {
    width: 100%;
    height: auto;
    align: center middle;
    margin: 1 0;
}

.export-buttons Button {
    width: 20%;
    margin: 0 1;
}

.pagination-input {
    width: 10%;
    margin: 0 1;
    text-align: center;
    background: #000088;
    color: #00FFFF;
    border: thick #FF00FF;
}

.pagination-display {
    width: 100%;
    text-align: center;
    color: #00FFFF;
    margin: 1 0;
    background: #110011;
    border: solid #FF00FF;
    padding: 1;
}

.action-buttons {
    width: 100%;
    height: auto;
    align: center middle;
    margin: 1 0;
    padding: 0;
}

.action-buttons Button {
    width: 25%;
    margin: 0 1;
}

.analytics-container {
    height: 1fr;
    width: 100%;
}

.compact-header {
    height: auto;
    min-height: 1;
    margin: 0 0 1 0;
}

.compact-button {
    height: 3;
    min-height: 3;
    margin: 0;
}

.menu-grid {
    layout: grid;
    grid-size: 2;
    grid-gutter: 1 2;
    width: 80%;
    height: auto;
    align: center middle;
    margin: 1 0;
}

.menu-grid Button {
    width: 100%;
}
"""

class WowFactorHeader(Static):
    """Custom Header Widget for WowFactor TUI."""
    def on_mount(self) -> None:
        self.update(self._render_header("Loading..."))

    def _render_header(self, dynamic_text: str) -> str:
        gradient_text = colorize_text_gradient(dynamic_text, RETRO_GRADIENT_COLORS)
        return f"[bold magenta]WowFactor Benchmark Utility[/]  |  {gradient_text}"

    def update_title(self, new_title: str) -> None:
        self.update(self._render_header(new_title))


class DataExportMixin:
    """Mixin to provide CSV and JSON export functionality to Screens."""

    def export_data(self, data: List[Dict], table: DataTable, export_type: str, filename_prefix: str) -> None:
        """
        Main entry point for exporting data.
        
        Args:
            data: List of dictionaries (source of truth for JSON).
            table: DataTable instance (source of truth for CSV columns).
            export_type: 'csv' or 'json'.
            filename_prefix: Prefix for the output filename.
        """
        import datetime
        import logging

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

    def _write_csv(self, table: DataTable, filename: str) -> None:
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


class MainMenuScreen(Screen):
    BINDINGS = [
        ("q", "quit_app", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Container(classes="main-menu-container"):
            yield WowFactorHeader(id="app-header")
            with Container(classes="menu-grid"):
                yield Button("Run New Benchmark", id="run_single_benchmark", variant="primary")
                yield Button("Run Batch Benchmark", id="run_batch_benchmark", variant="primary")
                yield Button("View Best Score per Machine", id="view_best_scores", variant="primary")
                yield Button("Compare a Specific CPU", id="compare_cpu", variant="primary")
                yield Button("View All Scores (Full List)", id="view_all_scores", variant="primary")
                yield Button("View Analytics", id="view_analytics", variant="primary")
                yield Button("Clear Invalid Scores", id="clear_invalid_confirm", variant="error")
                yield Button("Quit", id="quit_app", variant="default")
            yield Static("Awaiting command>", id="command_prompt")

    def on_mount(self) -> None:
        self.query_one("#app-header", WowFactorHeader).update_title("BENCHMARK INTERFACE")

    def action_quit_app(self) -> None:
        self.app.exit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses on this screen."""
        if event.button.id == "quit_app":
            self.action_quit_app()
        elif event.button.id == "run_single_benchmark":
            self.app.push_screen(RunSingleBenchmarkScreen())
            event.stop() # Stop event propagation
        elif event.button.id == "run_batch_benchmark":
            self.app.push_screen(RunBatchBenchmarkScreen())
            event.stop() # Stop event propagation
        elif event.button.id == "view_best_scores":
            self.app.push_screen(ViewBestScoresScreen())
            event.stop() # Stop event propagation
        elif event.button.id == "view_all_scores":
            self.app.push_screen(ViewAllScoresScreen())
            event.stop() # Stop event propagation
        elif event.button.id == "clear_invalid_confirm":
            # Check how many invalid files exist before showing confirmation
            import os
            if not os.path.exists(BENCHMARK_DIR):
                invalid_count = 0
            else:
                # Count all JSON files and check which ones are invalid
                import json
                invalid_count = 0
                for filename in os.listdir(BENCHMARK_DIR):
                    if filename.endswith('.json'):
                        try:
                            with open(os.path.join(BENCHMARK_DIR, filename), 'r') as f:
                                data = json.load(f)
                                # Check if it has required fields
                                if 'ops_per_second' not in data or 'system' not in data or 'processor_model' not in data.get('system', {}):
                                    invalid_count += 1
                        except (json.JSONDecodeError, KeyError):
                            invalid_count += 1
            self.app.push_screen(ClearInvalidScoresConfirmationScreen(invalid_count))
            event.stop() # Stop event propagation
        elif event.button.id == "compare_cpu":
            self.app.push_screen(CompareCPUScreen())
            event.stop() # Stop event propagation
        elif event.button.id == "view_analytics":
            self.app.push_screen(AnalyticsScreen())
            event.stop()
        else: # For other buttons, update prompt and potentially stop event
            self.query_one("#command_prompt", Static).update(f"Command: {event.button.label} pressed!")
            event.stop() # Stop event propagation for other buttons too


class RunSingleBenchmarkScreen(Screen):
    BINDINGS = [
        ("b", "go_back", "Back to Main Menu"),
        ("q", "quit_app", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="run-benchmark-screen"):
            yield WowFactorHeader(id="app-header")
            yield Static(colorize_text_gradient("RUN NEW BENCHMARK", RETRO_GRADIENT_COLORS), classes="title")
            yield Static("Enter test duration in seconds (0 for infinite):")
            yield Input(value="15", placeholder="Duration (seconds)", id="duration_input", type="integer")
            yield Static(f"Number of Threads (Max: {multiprocessing.cpu_count()}):")
            yield Input(value="1", placeholder="Threads", id="threads_input", type="integer")
            with Horizontal(classes="action-buttons"):
                yield Button("Start", id="start_benchmark", variant="primary")
                yield Button("Stop", id="stop_benchmark", variant="error", disabled=True)
            yield Static("Progress: Ready to start...", id="progress_display")
            yield Static("", id="result_summary_display", classes="result-summary")
            yield Markdown("", id="result_markdown_display") # Using Markdown for flexible output
            with Horizontal(classes="action-buttons"):
                yield Button("Back", id="back_to_main_menu", variant="default")

    def on_mount(self) -> None:
        self.query_one("#app-header", WowFactorHeader).update_title("BENCHMARK")
        self.query_one("#stop_benchmark", Button).display = False # Hide stop button initially
        self.query_one("#result_summary_display", Static).display = False
        self.query_one("#result_markdown_display", Markdown).display = False

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start_benchmark":
            self.start_benchmark_run()
        elif event.button.id == "stop_benchmark":
            self.stop_benchmark_run()
            event.stop()
        elif event.button.id == "back_to_main_menu":
            self.action_go_back()
            event.stop()
        elif event.button.id == "quit_app":
            self.app.exit() # Allow quitting from this screen too
            event.stop()

    def start_benchmark_run(self) -> None:
        duration_input_widget = self.query_one("#duration_input", Input)
        threads_input_widget = self.query_one("#threads_input", Input)
        duration_str = duration_input_widget.value
        threads_str = threads_input_widget.value
        
        # Validate that input is an integer (including zero for infinite)
        try:
            duration = int(duration_str)
        except ValueError:
            self.query_one("#progress_display", Static).update("[red]Invalid duration. Please enter a positive integer or 0 for infinite.[/red]")
            return
            
        # Validate range: must be non-negative (positive integer or zero)
        if duration < 0:
            self.query_one("#progress_display", Static).update("[red]Invalid duration. Please enter a positive integer or 0 for infinite.[/red]")
            return

        # Validate threads
        try:
            num_threads = int(threads_str)
        except ValueError:
            self.query_one("#progress_display", Static).update("[red]Invalid thread count. Please enter a positive integer.[/red]")
            return
        
        if num_threads < 1:
            self.query_one("#progress_display", Static).update("[red]Thread count must be at least 1.[/red]")
            return

        is_infinite = (duration == 0)

        self.query_one("#start_benchmark", Button).disabled = True
        self.query_one("#stop_benchmark", Button).disabled = False
        self.query_one("#stop_benchmark", Button).display = True
        self.query_one("#back_to_main_menu", Button).disabled = True
        self.query_one("#result_summary_display", Static).display = False
        self.query_one("#result_markdown_display", Markdown).display = False
        self.query_one("#progress_display", Static).update("Benchmark started...")

        self.benchmark_worker = self.run_worker(
            self._benchmark_worker_function(duration, is_infinite, num_threads),
            thread=True,
            group="benchmark_workers",
        )

    # Add method to access core function
    def execute_single_benchmark_run(self, duration: float, is_infinite: bool, num_threads: int, progress_callback):
        return execute_single_benchmark_run(duration, is_infinite, num_threads=num_threads, progress_callback=progress_callback)

    # Add method to access core function
    def format_large_number(self, num: float):
        return format_large_number(num)

    def stop_benchmark_run(self) -> None:
        if hasattr(self, 'benchmark_worker') and self.benchmark_worker.is_running:
            self.benchmark_worker.cancel() # This will raise WorkerCancelled on the worker thread
            self.query_one("#progress_display", Static).update("Stopping benchmark (please wait)...")

    async def _benchmark_worker_function(self, duration: float, is_infinite: bool, num_threads: int):
        total_ops = 0
        ops_per_second = 0.0
        try:
            def progress_callback(current_total_ops: int, current_time: float, start_time: float):
                # Check for cancellation
                if hasattr(self, 'benchmark_worker') and self.benchmark_worker.is_cancelled:
                    raise Exception("WorkerCancelled")

                nonlocal total_ops, ops_per_second
                total_ops = current_total_ops
                elapsed_time = current_time - start_time
                ops_per_second = total_ops / elapsed_time if elapsed_time > 0 else 0
                self.post_message(BenchmarkProgress(total_ops, ops_per_second))

            result = self.execute_single_benchmark_run(duration, is_infinite, num_threads, progress_callback)
            self.post_message(BenchmarkCompletion(result))
        except Exception as e:
            # Check specifically for WorkerCancelled exception from Textual
            if "WorkerCancelled" in str(type(e)) or "cancelled" in str(e).lower():
                logging.info("Benchmark worker was cancelled by user.")
                self.post_message(BenchmarkCompletion({"message": "Benchmark interrupted by user."}, interrupted=True))
            else:
                # Log detailed error information for debugging
                error_msg = f"Benchmark worker failed unexpectedly: {type(e).__name__}: {str(e)}"
                logging.error(error_msg, exc_info=True)
                
                # Provide a more user-friendly message that includes the specific error type
                if hasattr(e, '__cause__') and e.__cause__:
                    cause_type = type(e.__cause__).__name__
                    cause_msg = str(e.__cause__)
                    friendly_error = f"Benchmark failed due to {cause_type}: {cause_msg}"
                else:
                    friendly_error = "Benchmark worker encountered an unexpected error. Please check the logs for details."
                
                self.post_message(BenchmarkCompletion({"error": str(e), "message": friendly_error, "error_type": type(e).__name__}, interrupted=True))

    def on_benchmark_progress(self, message: BenchmarkProgress) -> None:
        self.query_one("#progress_display", Static).update(
            f"Progress: [green]Ops: {format_large_number(message.total_ops)}[/green] | [yellow]Ops/sec: {format_large_number(message.ops_per_second)}[/yellow]"
        )

    def on_benchmark_completion(self, message: BenchmarkCompletion) -> None:
        result_data = message.result_data
        status_message = "Benchmark completed!"
        if message.interrupted:
            status_message = "[orange_red1]Benchmark stopped prematurely![/orange_red1]"
            if "message" in result_data:
                status_message += f"\n[red]{result_data['message']}[/red]"
            elif "error" in result_data:
                # Display more detailed error information
                error_type = result_data.get('error_type', 'Unknown')
                error_msg = result_data.get('error', '')
                status_message += f"\nError: [red]{error_type}: {error_msg}[/red]"

        self.query_one("#progress_display", Static).update(status_message)
        self.query_one("#start_benchmark", Button).disabled = False
        self.query_one("#stop_benchmark", Button).disabled = True
        self.query_one("#stop_benchmark", Button).display = False
        self.query_one("#back_to_main_menu", Button).disabled = False

        if "total_operations" in result_data and not message.interrupted: # Only display full summary if not interrupted and results are valid
            summary_text = (
                f"[neon-green-rank]Total Operations: [green]{format_large_number(result_data['total_operations'])}[/green]\n"
                f"[neon-green-rank]Operations Per Second: [green]{format_large_number(result_data['ops_per_second'])}[/green]\n"
                f"[neon-green-rank]Duration: [green]{result_data['duration_seconds']:.2f}s[/green]\n"
                f"[neon-green-rank]Threads: [green]{result_data.get('num_threads', 1)}[/green]\n"
                f"[neon-green-rank]CPU: [green]{result_data['system']['processor_model']} @ {result_data['system']['processor_frequency']}[/green]\n"
                f"[neon-green-rank]Platform: [green]{result_data['system']['platform']}[/green]\n"
                f"[neon-green-rank]Results file: [blue]{result_data['file_path']}[/blue]"
            )
        else:
            summary_text = "[red]Benchmark failed or produced no results.[/red]"
            if message.interrupted and "message" not in result_data: # If interrupted and no specific error message, add a generic one
                 summary_text = "[red]Benchmark was interrupted or failed to produce complete results.[/red]"

        self.query_one("#result_summary_display", Static).update(summary_text)
        self.query_one("#result_summary_display", Static).display = True

        # For detailed results, format as Markdown or use a DataTable
        # For simplicity, let's use Markdown for now.
        markdown_output = "### Detailed Benchmark Results\n\n"
        if result_data:
            markdown_output += "```json\n"
            markdown_output += json.dumps(result_data, indent=2)
            markdown_output += "\n```"
        else:
            markdown_output += "No detailed results available."
        
        self.query_one("#result_markdown_display", Markdown).update(markdown_output)
        self.query_one("#result_markdown_display", Markdown).display = True


class RunBatchBenchmarkScreen(Screen):
    BINDINGS = [
        ("b", "go_back", "Back to Main Menu"),
        ("q", "quit_app", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="run-benchmark-screen"):
            yield WowFactorHeader(id="app-header")
            yield Static(colorize_text_gradient("RUN BATCH BENCHMARK", RETRO_GRADIENT_COLORS), classes="title")
            yield Static("Number of batch runs (2-100):")
            yield Input(value="5", placeholder="Batch Runs (2-100)", id="batch_runs_input", type="integer")
            yield Static("Duration for each run in seconds (default: 15):")
            yield Input(value="15", placeholder="Duration (seconds)", id="duration_input", type="integer")
            with Horizontal(classes="action-buttons"):
                yield Button("Start Batch", id="start_batch_benchmark", variant="primary")
                yield Button("Stop Batch", id="stop_batch_benchmark", variant="error", disabled=True)
            yield Static("Current Batch: Ready to start...", id="batch_number_display")
            yield Static("Progress: Ready for run 1...", id="progress_display")
            yield Static("", id="cooldown_display")
            yield Static("", id="batch_summary_display", classes="result-summary")
            yield Markdown("", id="batch_markdown_display")
            with Horizontal(classes="action-buttons"):
                yield Button("Back", id="back_to_main_menu", variant="default")

    def on_mount(self) -> None:
        self.query_one("#app-header", WowFactorHeader).update_title("BATCH BENCHMARK")
        self.query_one("#stop_batch_benchmark", Button).display = False
        self.query_one("#batch_summary_display", Static).display = False
        self.query_one("#batch_markdown_display", Markdown).display = False
        self.query_one("#cooldown_display", Static).display = False

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start_batch_benchmark":
            self.start_batch_benchmark()
            event.stop()
        elif event.button.id == "stop_batch_benchmark":
            self.stop_batch_benchmark()
            event.stop()
        elif event.button.id == "back_to_main_menu":
            self.action_go_back()
            event.stop()
        elif event.button.id == "quit_app":
            self.app.exit()
            event.stop()

    def start_batch_benchmark(self) -> None:
        batch_runs_input = self.query_one("#batch_runs_input", Input)
        duration_input = self.query_one("#duration_input", Input)

        # Validate batch runs input
        try:
            num_batch_runs = int(batch_runs_input.value)
        except ValueError:
            self.query_one("#progress_display", Static).update("[red]Invalid number of batch runs. Please enter an integer between 2 and 100.[/red]")
            return
            
        # Validate range for batch runs: must be between 2 and 100 inclusive
        if not (2 <= num_batch_runs <= 100):
            self.query_one("#progress_display", Static).update("[red]Number of batch runs must be between 2 and 100.[/red]")
            return

        # Validate duration per run input
        try:
            duration_per_run = int(duration_input.value)
        except ValueError:
            self.query_one("#progress_display", Static).update("[red]Invalid duration. Please enter a positive integer for duration per run.[/red]")
            return
            
        # Validate range for duration per run: must be positive (greater than 0)
        if duration_per_run <= 0:
            self.query_one("#progress_display", Static).update("[red]Duration per run must be a positive integer.[/red]")
            return

        self.query_one("#start_batch_benchmark", Button).disabled = True
        self.query_one("#stop_batch_benchmark", Button).disabled = False
        self.query_one("#stop_batch_benchmark", Button).display = True
        self.query_one("#back_to_main_menu", Button).disabled = True
        self.query_one("#batch_summary_display", Static).display = False
        self.query_one("#batch_markdown_display", Markdown).display = False
        self.query_one("#cooldown_display", Static).display = False

        self.query_one("#batch_number_display", Static).update(f"Current Batch: Starting {num_batch_runs} runs...")
        self.query_one("#progress_display", Static).update("Progress: Initializing...")

        self.batch_worker_instance = self.run_worker(
            self._batch_benchmark_worker_function(num_batch_runs, duration_per_run),
            thread=True,
            group="batch_benchmark_workers",
        )

    # Add method to access core function
    def execute_single_benchmark_run(self, duration: float, is_infinite: bool, progress_callback):
        # Pass default num_threads=1 for batch runs
        return execute_single_benchmark_run(duration, is_infinite, progress_callback=progress_callback)

    # Add method to access core function
    def format_large_number(self, num: float):
        return format_large_number(num)

    def stop_batch_benchmark(self) -> None:
        if hasattr(self, 'batch_worker_instance') and self.batch_worker_instance.is_running:
            self.batch_worker_instance.cancel()
            self.query_one("#progress_display", Static).update("Stopping batch benchmark (please wait)...")

    async def _batch_benchmark_worker_function(self, num_batch_runs: int, duration_per_run: int, cooldown_duration: int = 5):
        all_results = []
        try:
            for i in range(1, num_batch_runs + 1):
                # Check for cancellation before starting run
                if hasattr(self, 'batch_worker_instance') and self.batch_worker_instance.is_cancelled:
                    raise Exception("WorkerCancelled")

                self.post_message(BatchBenchmarkProgress(i, num_batch_runs, 0, 0.0))
                # Removed unsafe UI update: self.query_one("#progress_display", Static).update(...)
                
                current_run_ops = 0
                current_run_ops_per_second = 0.0
                
                def progress_callback(total_ops: int, current_time: float, start_time: float):
                    # Check for cancellation during run
                    if hasattr(self, 'batch_worker_instance') and self.batch_worker_instance.is_cancelled:
                        raise Exception("WorkerCancelled")

                    nonlocal current_run_ops, current_run_ops_per_second
                    current_run_ops = total_ops
                    elapsed = current_time - start_time
                    current_run_ops_per_second = total_ops / elapsed if elapsed > 0 else 0.0
                    self.post_message(BatchBenchmarkProgress(i, num_batch_runs, current_run_ops, current_run_ops_per_second))
                
                result = self.execute_single_benchmark_run(duration_per_run, False, progress_callback)
                all_results.append(result)
                
                if i < num_batch_runs:
                    for remaining_cooldown in range(cooldown_duration, 0, -1):
                        # Check for cancellation during cooldown
                        if hasattr(self, 'batch_worker_instance') and self.batch_worker_instance.is_cancelled:
                            raise Exception("WorkerCancelled")

                        self.post_message(CooldownMessage(i, num_batch_runs, remaining_cooldown))
                        time.sleep(1) # Safe to sleep in worker thread
                    
                    # Update to 0 or clear message at end of cooldown if needed,
                    # but next loop iteration will update progress immediately
        except Exception as e:
            # Check specifically for WorkerCancelled exception from Textual
            if "WorkerCancelled" in str(type(e)) or "cancelled" in str(e).lower():
                logging.info("Batch benchmark worker was cancelled by user.")
                self.post_message(BatchBenchmarkCompletion(all_results, num_batch_runs, interrupted=True))
                return
            else:
                # Log detailed error information for debugging with run context
                error_msg = f"Batch benchmark worker failed during run {i}: {type(e).__name__}: {str(e)}"
                logging.error(error_msg, exc_info=True)
                
                # Provide a more user-friendly message that includes the specific error type and run number
                if hasattr(e, '__cause__') and e.__cause__:
                    cause_type = type(e.__cause__).__name__
                    cause_msg = str(e.__cause__)
                    friendly_error = f"Batch benchmark failed during run {i} due to {cause_type}: {cause_msg}"
                else:
                    friendly_error = f"Batch benchmark worker encountered an unexpected error on run {i}. Please check the logs for details."
                
                self.post_message(BatchBenchmarkCompletion(all_results, num_batch_runs, interrupted=True))
                return
        
        self.post_message(BatchBenchmarkCompletion(all_results, num_batch_runs))
    
    def on_batch_benchmark_progress(self, message: BatchBenchmarkProgress) -> None:
        self.query_one("#batch_number_display", Static).update(
            f"BATCH RUN {message.batch_run_number} OF {message.total_batch_runs}"
        )
        self.query_one("#progress_display", Static).update(
            f"Progress: [green]Ops: {format_large_number(message.total_ops)}[/green] | [yellow]Ops/sec: {format_large_number(message.ops_per_second)}[/yellow]"
        )
        self.query_one("#cooldown_display", Static).display = False

    def on_cooldown_message(self, message: CooldownMessage) -> None:
        self.query_one("#cooldown_display", Static).update(
            f"[yellow]Cooldown: {message.cooldown_seconds}s until next run (BATCH RUN {message.current_batch_run + 1} OF {message.total_batch_runs})...[/yellow]"
        )
        self.query_one("#cooldown_display", Static).display = True

    def on_batch_benchmark_completion(self, message: BatchBenchmarkCompletion) -> None:
        status_message = "BATCH COMPLETE. All benchmark runs have finished."
        if message.interrupted:
            status_message = "[orange_red1]BATCH INTERRUPTED. Not all runs completed.[/orange_red1]"
            # Add error information to the status message if available
            if hasattr(message, 'results') and len(message.results) > 0:
                last_result = message.results[-1]
                if "error" in last_result:
                    error_type = last_result.get('error_type', 'Unknown')
                    error_msg = last_result.get('error', '')
                    status_message += f"\n[red]Last run failed with {error_type}: {error_msg}[/red]"

        self.query_one("#batch_number_display", Static).update(status_message)
        self.query_one("#progress_display", Static).update("Batch process finished.")
        self.query_one("#start_batch_benchmark", Button).disabled = False
        self.query_one("#stop_batch_benchmark", Button).disabled = True
        self.query_one("#stop_batch_benchmark", Button).display = False
        self.query_one("#back_to_main_menu", Button).disabled = False
        self.query_one("#cooldown_display", Static).display = False

        summary_text = f"[neon-green-rank]Total {len(message.results)} runs completed.\n[/neon-green-rank]"
        if message.results:
            total_ops_sum = sum(r.get('total_operations', 0) for r in message.results)
            avg_ops_per_second = sum(r.get('ops_per_second', 0.0) for r in message.results) / len(message.results) if message.results else 0.0
            
            summary_text += (
                f"[neon-green-rank]Overall Average Operations Per Second: [green]{format_large_number(avg_ops_per_second)}[/green]\n"
                f"[neon-green-rank]Combined Total Operations: [green]{format_large_number(total_ops_sum)}[/green]\n"
            )
        else:
            summary_text += "[red]No results were recorded for this batch.[/red]"

        self.query_one("#batch_summary_display", Static).update(summary_text)
        self.query_one("#batch_summary_display", Static).display = True

        markdown_output = "### Detailed Batch Benchmark Results\n\n"
        if message.results:
            for i, result_data in enumerate(message.results):
                markdown_output += f"#### Run {i+1}\n"
                markdown_output += "```json\n"
                markdown_output += json.dumps(result_data, indent=2)
                markdown_output += "\n```\n"
        else:
            markdown_output += "No detailed results available."
        
        self.query_one("#batch_markdown_display", Markdown).update(markdown_output)


class ViewBestScoresScreen(DataExportMixin, Screen):
    BINDINGS = [
        ("b", "go_back", "Back to Main Menu"),
        ("q", "quit_app", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Container():
            yield WowFactorHeader(id="app-header")
            yield Static(colorize_text_gradient("BEST SCORES PER MACHINE", RETRO_GRADIENT_COLORS), classes="title")
            yield Static("Search:", id="search_label")
            yield Input(placeholder="Search CPU model, platform, or timestamp...", id="search_input", classes="search-input")
            yield Static("Loading best scores...", id="loading_display")
            yield DataTable(id="best_scores_table", classes="result-table")
            with Horizontal(classes="action-buttons"):
                yield Button("Export CSV", id="export_csv", variant="primary")
                yield Button("Export JSON", id="export_json", variant="primary")
                yield Button("Back", id="back_to_main_menu", variant="default")

    def on_mount(self) -> None:
        self.query_one("#app-header", WowFactorHeader).update_title("BEST SCORES")
        self.current_data = []
        self.load_data()

    def load_data(self) -> None:
        """Load and display the best scores per machine."""
        # Show loading indicator
        self.query_one("#loading_display", Static).display = True
        self.query_one("#best_scores_table", DataTable).display = False
        
        # Fetch data from core using a worker to avoid blocking UI
        self.run_worker(self._load_data_worker(), thread=True, group="data_loading")
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        search_term = event.input.value.strip()
        if not hasattr(self, 'original_scores'):
            # If we don't have original scores yet, do nothing
            return
            
        # Debounce the filtering to improve performance during rapid typing
        self._debounced_search(search_term)
    
    def _debounced_search(self, search_term: str) -> None:
        """Perform debounced search to improve performance."""
        # Cancel any existing debounce timer
        if hasattr(self, '_search_timer'):
            self._search_timer.cancel()
        
        # Set a new timer for 300ms debounce
        from asyncio import sleep
        async def delayed_search():
            await sleep(0.3)  # 300ms delay
            # Since we are already in the async loop (create_task), we can call directly.
            # call_from_thread is only for when we are in a different thread.
            self._perform_search(search_term)
        
        # Store reference to timer so we can cancel it if needed
        import asyncio
        self._search_timer = asyncio.create_task(delayed_search())
    
    def _perform_search(self, search_term: str) -> None:
        """Perform the actual search filtering."""
        try:
            # Show loading indicator during filtering
            if search_term:
                self.query_one("#loading_display", Static).update(f"Filtering results for '{search_term}'...")
            else:
                self.query_one("#loading_display", Static).update("Showing all results...")
            self.query_one("#loading_display", Static).display = True
            self.query_one("#best_scores_table", DataTable).display = False
            
            # Filter the data based on search term
            filtered_scores = []
            if search_term:
                search_lower = search_term.lower()
                for score in self.original_scores:
                    cpu_model = score.get('system', {}).get('processor_model', '').lower()
                    platform = score.get('system', {}).get('platform', '').lower()
                    timestamp = score.get('timestamp', '').lower()
                    ops_per_second = str(score.get('ops_per_second', '')).lower()
                    
                    # Search across all relevant fields
                    if (search_lower in cpu_model or
                        search_lower in platform or
                        search_lower in timestamp or
                        search_lower in ops_per_second):
                        filtered_scores.append(score)
            else:
                # If no search term, show all scores
                filtered_scores = self.original_scores
            
            # Update the table with filtered data
            self.current_data = filtered_scores
            self._update_table_with_scores(filtered_scores)
            
            # Hide loading indicator after filtering
            self.query_one("#loading_display", Static).display = False
            self.query_one("#best_scores_table", DataTable).display = True
        except Exception as e:
            logging.error(f"Error during search filtering: {e}")
            # Show error message if filtering fails
            self.query_one("#loading_display", Static).update("[red]Error filtering results[/red]")
            self.query_one("#loading_display", Static).display = True
            self.query_one("#best_scores_table", DataTable).display = False

    async def _load_data_worker(self):
        """Worker function for loading best scores."""
        try:
            # Fetch data from core
            best_scores = get_best_score_per_machine()

            # Store original scores for filtering
            self.original_scores = best_scores
            self.current_data = best_scores
            
            # Update the UI on the main thread using post_message
            self.post_message(DataLoadComplete(best_scores))
        except Exception as e:
            logging.error(f"Error loading best scores: {e}")
            self.post_message(DataLoadError())

    def _update_table_with_scores(self, best_scores):
        """Update table with loaded scores."""
        table = self.query_one("#best_scores_table", DataTable)
        
        # Clear existing data
        table.clear()
        
        # Add columns with appropriate widths for better display
        table.add_column("Rank", key="rank", width=5)
        table.add_column("CPU Model", key="cpu_model")  # No fixed width to allow dynamic sizing
        table.add_column("Platform", key="platform", width=12)
        table.add_column("Threads", key="num_threads", width=8)
        table.add_column("Ops/Second", key="ops_per_second", width=15)
        table.add_column("Timestamp", key="timestamp", width=20)  # Limit timestamp width
        
        # Add rows with rank indicators
        for i, score in enumerate(best_scores):
            rank = i + 1
            cpu_model = score.get('system', {}).get('processor_model', 'N/A')
            platform = score.get('system', {}).get('platform', 'N/A')
            num_threads = str(score.get('num_threads', 1))
            ops_per_second = score.get('ops_per_second', 0)
            timestamp = score.get('timestamp', 'N/A')
            
            # Format the ops_per_second value
            formatted_ops = format_large_number(ops_per_second)
            
            # Apply rank styling
            if rank == 1:
                rank_text = f"[gold-rank]#{rank}[/gold-rank]"
            elif rank == 2:
                rank_text = f"[silver-rank]#{rank}[/silver-rank]"
            elif rank == 3:
                rank_text = f"[bronze-rank]#{rank}[/bronze-rank]"
            else:
                rank_text = f"[dark-blue-rank]#{rank}[/dark-blue-rank]"
            
            table.add_row(
                rank_text,
                cpu_model,
                platform,
                num_threads,
                formatted_ops,
                timestamp
            )
        
        # Make the Ops/Second column sortable by using the numeric value for sorting
        # We need to store the numeric value for proper sorting
        table.sort("ops_per_second", reverse=True)
        # Set column widths based on content after adding rows
        self._adjust_column_widths_and_wrap_names(table)
        
        # Hide loading indicator and show table
        self.query_one("#loading_display", Static).display = False
        self.query_one("#best_scores_table", DataTable).display = True
    

    def _adjust_column_widths_and_wrap_names(self, table):
        """Adjust column widths based on content to prevent overflow and wrap/truncate long CPU names."""
        # Get the maximum width needed for each column
        max_widths = {}
        
        # Initialize with header widths from the actual Column objects
        for column_key, column in table.columns.items():
            max_widths[column_key] = len(str(column.label))
        
        # Check row data for maximum width
        for row in table.rows:
            for key in table.columns.keys():  # Iterate over ColumnKeys, not ColumnKey objects
                cell_value = table.get_cell(row, key)
                if key not in max_widths: # This should not happen if headers are added correctly
                    max_widths[key] = 0
                current_width = len(str(cell_value))
                max_widths[key] = max(max_widths[key], current_width)
        
        # Adjust column widths (with reasonable limits)
        for column_key, column_obj in table.columns.items(): # Iterate over ColumnKeys and Column objects
            if column_key == "cpu_model":
                # For CPU model names, we want to allow more space but not too much
                new_width = min(max_widths[column_key], 60)  # Limit to 60 chars max for better readability
                column_obj.width = new_width
            elif column_key == "timestamp":
                # Timestamps should be limited to prevent overflow
                new_width = min(max_widths[column_key], 25)
                column_obj.width = new_width
            else:
                # For other columns, use reasonable limits
                if column_key == "rank":
                    column_obj.width = 5
                elif column_key == "platform":
                    column_obj.width = min(max_widths[column_key], 15)
                elif column_key == "num_threads":
                    column_obj.width = 8
                elif column_key == "ops_per_second":
                    column_obj.width = min(max_widths[column_key], 20)
        
        # Apply text wrapping for CPU model column if needed
        # Note: Textual DataTable doesn't support native text wrapping,
        # but we can truncate long names with ellipsis
        self._wrap_long_cpu_names(table)

    def _wrap_long_cpu_names(self, table):
        """Wrap or truncate long CPU model names to prevent overflow."""
        # Check if any CPU model name is too long and needs truncation
        for row in table.rows:
            cpu_model_value = table.get_cell(row, "cpu_model")
            if len(str(cpu_model_value)) > 60:  # Truncate if longer than 60 chars (matching new max width)
                truncated_name = str(cpu_model_value)[:57] + "..."
                table.set_cell(row, "cpu_model", truncated_name)

    def _show_error_message(self):
        """Show error message if data loading fails."""
        self.query_one("#loading_display", Static).update("[red]Error loading scores. Please try again.[/red]")
        self.query_one("#loading_display", Static).display = True
        self.query_one("#best_scores_table", DataTable).display = False

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def on_data_load_complete(self, message: DataLoadComplete) -> None:
        """Handle successful data loading."""
        self._update_table_with_scores(message.data)
    
    def on_data_load_error(self, message: DataLoadError) -> None:
        """Handle data loading error."""
        self._show_error_message()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "export_csv":
            # Pass current_data (filtered dataset)
            self.export_data(self.current_data, self.query_one("#best_scores_table", DataTable), "csv", "best_scores")
            event.stop()
        elif event.button.id == "export_json":
            # Pass current_data (filtered dataset)
            self.export_data(self.current_data, self.query_one("#best_scores_table", DataTable), "json", "best_scores")
            event.stop()
        elif event.button.id == "back_to_main_menu":
            self.action_go_back()
            event.stop()
        elif event.button.id == "quit_app":
            self.app.exit()
            event.stop()



class CompareCPUScreen(DataExportMixin, Screen):
    BINDINGS = [
        ("b", "go_back", "Back to Main Menu"),
        ("q", "quit_app", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Container():
            yield WowFactorHeader(id="app-header")
            yield Static(colorize_text_gradient("COMPARE SPECIFIC CPU", RETRO_GRADIENT_COLORS), classes="title")
            yield Static("Enter CPU model name to compare:")
            yield Input(placeholder="CPU Model Name", id="cpu_model_input")
            yield Button("Compare CPU", id="compare_cpu_button", variant="primary")
            yield Static("Search:", id="search_label")
            yield Input(placeholder="Search platform or timestamp...", id="search_input", classes="search-input")
            yield Static("Loading CPU scores...", id="loading_display")
            yield DataTable(id="cpu_comparison_table", classes="result-table")
            with Horizontal(classes="action-buttons"):
                yield Button("Export CSV", id="export_csv", variant="primary")
                yield Button("Export JSON", id="export_json", variant="primary")
                yield Button("Back", id="back_to_main_menu", variant="default")

    def on_mount(self) -> None:
        self.query_one("#app-header", WowFactorHeader).update_title("CPU COMPARISON")
        self.current_data = []

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def on_data_load_complete(self, message: DataLoadComplete) -> None:
        """Handle successful data loading."""
        self._update_comparison_table(message.data)
    
    def on_data_load_error(self, message: DataLoadError) -> None:
        """Handle data loading error."""
        self._show_error_message()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "compare_cpu_button":
            self.compare_cpu()
        elif event.button.id == "export_csv":
            self.export_data(self.current_data, self.query_one("#cpu_comparison_table", DataTable), "csv", "cpu_comparison")
            event.stop()
        elif event.button.id == "export_json":
            self.export_data(self.current_data, self.query_one("#cpu_comparison_table", DataTable), "json", "cpu_comparison")
            event.stop()
        elif event.button.id == "back_to_main_menu":
            self.action_go_back()
            event.stop()
        elif event.button.id == "quit_app":
            self.app.exit()
            event.stop()

    def compare_cpu(self) -> None:
        input_widget = self.query_one("#cpu_model_input", Input)
        cpu_model_name = input_widget.value.strip()
        
        if not cpu_model_name:
            self.query_one("#cpu_comparison_table", DataTable).clear()
            # Add columns first if they don't exist
            table = self.query_one("#cpu_comparison_table", DataTable)
            if not table.columns:
                table.add_column("Rank", key="rank", width=5)
                table.add_column("Platform", key="platform", width=12)
                table.add_column("Threads", key="num_threads", width=8)
                table.add_column("Ops/Second", key="ops_per_second", width=15)
                table.add_column("Timestamp", key="timestamp", width=20)
            
            # Add row with proper column count when no CPU model is entered
            table.add_row(
                "[dark-blue-rank]#0[/dark-blue-rank]",  # Rank placeholder
                "Please enter a CPU model name",        # Platform placeholder (showing message)
                "N/A",                                  # Threads placeholder
                "0",                                    # Ops/Second placeholder
                "N/A"                                   # Timestamp placeholder
            )
            return
        
        # Show loading indicator
        self.query_one("#loading_display", Static).display = True
        self.query_one("#cpu_comparison_table", DataTable).display = False
        
        # Fetch data using worker to avoid blocking UI
        self.run_worker(self._compare_cpu_worker(cpu_model_name), thread=True, group="data_loading")
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        search_term = event.input.value.strip()
        if not hasattr(self, 'original_cpu_scores'):
            # If we don't have original scores yet, do nothing
            return
            
        # Debounce the filtering to improve performance during rapid typing
        self._debounced_search(search_term)
    
    def _debounced_search(self, search_term: str) -> None:
        """Perform debounced search to improve performance."""
        # Cancel any existing debounce timer
        if hasattr(self, '_search_timer'):
            self._search_timer.cancel()
        
        # Set a new timer for 300ms debounce
        from asyncio import sleep
        async def delayed_search():
            await sleep(0.3)  # 300ms delay
            # Since we are already in the async loop (create_task), we can call directly.
            # call_from_thread is only for when we are in a different thread.
            self._perform_search(search_term)
        
        # Store reference to timer so we can cancel it if needed
        import asyncio
        self._search_timer = asyncio.create_task(delayed_search())
    
    def _perform_search(self, search_term: str) -> None:
        """Perform the actual search filtering."""
        try:
            # Show loading indicator during filtering
            if search_term:
                self.query_one("#loading_display", Static).update(f"Filtering results for '{search_term}'...")
            else:
                self.query_one("#loading_display", Static).update("Showing all results...")
            self.query_one("#loading_display", Static).display = True
            self.query_one("#cpu_comparison_table", DataTable).display = False
            
            # Filter the data based on search term
            filtered_scores = []
            if search_term:
                search_lower = search_term.lower()
                for score in self.original_cpu_scores:
                    platform = score.get('system', {}).get('platform', '').lower()
                    timestamp = score.get('timestamp', '').lower()
                    
                    # Search across all relevant fields
                    if (search_lower in platform or
                        search_lower in timestamp):
                        filtered_scores.append(score)
            else:
                # If no search term, show all scores
                filtered_scores = self.original_cpu_scores
            
            # Update the table with filtered data
            self.current_data = filtered_scores
            self._update_comparison_table(filtered_scores)
            
            # Hide loading indicator after filtering
            self.query_one("#loading_display", Static).display = False
            self.query_one("#cpu_comparison_table", DataTable).display = True
        except Exception as e:
            logging.error(f"Error during search filtering: {e}")
            # Show error message if filtering fails
            self.query_one("#loading_display", Static).update("[red]Error filtering results[/red]")
            self.query_one("#loading_display", Static).display = True
            self.query_one("#cpu_comparison_table", DataTable).display = False

    async def _compare_cpu_worker(self, cpu_model_name):
       """Worker function for comparing CPU scores."""
       try:
           # Get scores for the specified CPU
           cpu_scores = get_scores_for_cpu(cpu_model_name)

           # Store original scores for filtering
           self.original_cpu_scores = cpu_scores
           self.current_data = cpu_scores
           
           # Update the UI on the main thread using post_message
           self.post_message(DataLoadComplete(cpu_scores))
       except Exception as e:
           logging.error(f"Error loading CPU scores: {e}")
           self.post_message(DataLoadError())

    def _update_comparison_table(self, cpu_scores):
        """Update comparison table with loaded scores."""
        table = self.query_one("#cpu_comparison_table", DataTable)
        table.clear()
        
        # Add columns with appropriate widths first
        table.add_column("Rank", key="rank", width=5)
        table.add_column("Platform", key="platform", width=12)
        table.add_column("Threads", key="num_threads", width=8)
        table.add_column("Ops/Second", key="ops_per_second", width=15)
        table.add_column("Timestamp", key="timestamp", width=20)

        if not cpu_scores:
            # Fix for ValueError when displaying "No scores found" message
            # Must add a row with the same number of columns as defined
            table.add_row(
                "[dark-blue-rank]#0[/dark-blue-rank]",  # Rank placeholder
                "N/A",                                  # Platform placeholder
                "N/A",                                  # Threads placeholder
                "0",                                    # Ops/Second placeholder
                "N/A"                                   # Timestamp placeholder
            )
            # Hide loading indicator and show table
            self.query_one("#loading_display", Static).display = False
            self.query_one("#cpu_comparison_table", DataTable).display = True
            return

        # Add rows with rank indicators
        for i, score in enumerate(cpu_scores):
            rank = i + 1
            platform = score.get('system', {}).get('platform', 'N/A')
            num_threads = str(score.get('num_threads', 1))
            ops_per_second = score.get('ops_per_second', 0)
            timestamp = score.get('timestamp', 'N/A')
            
            # Format the ops_per_second value
            formatted_ops = format_large_number(ops_per_second)
            
            # Apply rank styling
            if rank == 1:
                rank_text = f"[gold-rank]#{rank}[/gold-rank]"
            elif rank == 2:
                rank_text = f"[silver-rank]#{rank}[/silver-rank]"
            elif rank == 3:
                rank_text = f"[bronze-rank]#{rank}[/bronze-rank]"
            else:
                rank_text = f"[dark-blue-rank]#{rank}[/dark-blue-rank]"
            
            table.add_row(
                rank_text,
                platform,
                num_threads,
                formatted_ops,
                timestamp
            )

        # Sort by ops_per_second descending (highest first)
        table.sort("ops_per_second", reverse=True)
        
        # Set column widths based on content after adding rows
        self._adjust_column_widths_and_wrap_names(table)
        
        # Hide loading indicator and show table
        self.query_one("#loading_display", Static).display = False
        self.query_one("#cpu_comparison_table", DataTable).display = True

    def _adjust_column_widths_and_wrap_names(self, table):
        """Adjust column widths based on content to prevent overflow and wrap/truncate long CPU names."""
        # Get the maximum width needed for each column
        max_widths = {}
        
        # Initialize with header widths from the actual Column objects
        for column_key, column in table.columns.items():
            max_widths[column_key] = len(str(column.label))
        
        # Check row data for maximum width
        for row in table.rows:
            for key in table.columns.keys():  # Iterate over ColumnKeys
                cell_value = table.get_cell(row, key)
                if key not in max_widths: # This should not happen if headers are added correctly
                    max_widths[key] = 0
                current_width = len(str(cell_value))
                max_widths[key] = max(max_widths[key], current_width)
        
        # Adjust column widths (with reasonable limits)
        for column_key, column_obj in table.columns.items(): # Iterate over ColumnKeys and Column objects
            if column_key == "timestamp":
                # Timestamps should be limited to prevent overflow
                new_width = min(max_widths[column_key], 25)
                column_obj.width = new_width
            else:
                # For other columns, use reasonable limits
                if column_key == "rank":
                    column_obj.width = 5
                elif column_key == "platform":
                    column_obj.width = min(max_widths[column_key], 15)
                elif column_key == "num_threads":
                    column_obj.width = 8
                elif column_key == "ops_per_second":
                    column_obj.width = min(max_widths[column_key], 20)
    
    def _show_error_message(self):
        """Show error message if data loading fails."""
        self.query_one("#loading_display", Static).update("[red]Error loading CPU scores. Please try again.[/red]")
        self.query_one("#loading_display", Static).display = True
        self.query_one("#cpu_comparison_table", DataTable).display = False

class ViewAllScoresScreen(DataExportMixin, Screen):
    BINDINGS = [
        ("b", "go_back", "Back to Main Menu"),
        ("q", "quit_app", "Quit"),
        ("pageup", "previous_page", "Previous Page"),
        ("pagedown", "next_page", "Next Page"),
        ("home", "first_page", "First Page"),
        ("end", "last_page", "Last Page"),
        ("g", "goto_page", "Go to Page"),
    ]

    def __init__(self):
        super().__init__()
        # Initialize pagination attributes
        self.current_page = 1
        self.page_size = 50  # Increased from 20 to 50 for better UX
        self.total_pages = 1
        self.total_items = 0
        self.filtered_scores = []
        self.original_all_scores = []

    def compose(self) -> ComposeResult:
        with Container():
            yield WowFactorHeader(id="app-header")
            yield Static(colorize_text_gradient("ALL SCORES (FULL LIST)", RETRO_GRADIENT_COLORS), classes="title")
            yield Static("Search:", id="search_label")
            yield Input(placeholder="Search CPU model, platform, or timestamp...", id="search_input", classes="search-input")
            yield Static("Loading all scores...", id="loading_display")
            yield DataTable(id="all_scores_table", classes="result-table")
            
            # Enhanced pagination controls
            with Container(classes="pagination-controls"):
                yield Static("", id="pagination_info", classes="pagination-info")
                with Horizontal(classes="pagination-buttons"):
                    yield Button("First [Home]", id="first_page", variant="default")
                    yield Button("Previous [PgUp]", id="previous_page", variant="default")
                    yield Input(placeholder="Page #", id="page_input", classes="pagination-input")
                    yield Button("Go [G]", id="goto_page", variant="primary")
                    yield Button("Next [PgDn]", id="next_page", variant="default")
                    yield Button("Last [End]", id="last_page", variant="default")
                yield Static("", id="pagination_display", classes="pagination-display")

            with Horizontal(classes="action-buttons"):
                yield Button("Export CSV", id="export_csv", variant="primary")
                yield Button("Export JSON", id="export_json", variant="primary")
                yield Button("Back", id="back_to_main_menu", variant="default")

    def on_mount(self) -> None:
        self.query_one("#app-header", WowFactorHeader).update_title("ALL SCORES")
        self.current_data = [] # Keep for DataExportMixin compatibility if needed, but rely on self.filtered_scores
        # Set initial page input value
        self.query_one("#page_input", Input).value = str(self.current_page)
        self.load_data()

    def load_data(self) -> None:
        """Load and display all scores."""
        # Show loading indicator
        self.query_one("#loading_display", Static).display = True
        self.query_one("#all_scores_table", DataTable).display = False
        
        # Disable pagination controls during loading
        self._set_pagination_controls_enabled(False)

        # Fetch data from core using a worker to avoid blocking UI
        self.run_worker(self._load_all_data_worker(), thread=True, group="data_loading")
    
    def _set_pagination_controls_enabled(self, enabled: bool) -> None:
        """Enable or disable pagination controls."""
        try:
            self.query_one("#first_page", Button).disabled = not enabled
            self.query_one("#previous_page", Button).disabled = not enabled
            self.query_one("#next_page", Button).disabled = not enabled
            self.query_one("#last_page", Button).disabled = not enabled
            self.query_one("#goto_page", Button).disabled = not enabled
            self.query_one("#page_input", Input).disabled = not enabled
        except Exception:
            # Skip if controls don't exist yet
            pass

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        search_term = event.input.value.strip()
        if not hasattr(self, 'original_all_scores'):
            # If we don't have original scores yet, do nothing
            return
            
        # Debounce the filtering to improve performance during rapid typing
        self._debounced_search(search_term)
    
    def _debounced_search(self, search_term: str) -> None:
        """Perform debounced search to improve performance."""
        # Cancel any existing debounce timer
        if hasattr(self, '_search_timer'):
            self._search_timer.cancel()
        
        # Set a new timer for 300ms debounce
        from asyncio import sleep
        async def delayed_search():
            await sleep(0.3)  # 300ms delay
            # Since we are already in the async loop (create_task), we can call directly.
            # call_from_thread is only for when we are in a different thread.
            self._perform_search(search_term)
        
        # Store reference to timer so we can cancel it if needed
        import asyncio
        self._search_timer = asyncio.create_task(delayed_search())
    
    def _perform_search(self, search_term: str) -> None:
        """Perform the actual search filtering."""
        try:
            # Show loading indicator during filtering
            if search_term:
                self.query_one("#loading_display", Static).update(f"Filtering results for '{search_term}'...")
            else:
                self.query_one("#loading_display", Static).update("Showing all results...")
            self.query_one("#loading_display", Static).display = True
            
            # Disable pagination controls during filtering
            self._set_pagination_controls_enabled(False)

            # Filter the data based on search term
            filtered_scores = []
            if search_term:
                search_lower = search_term.lower()
                for score in self.original_all_scores:
                    cpu_model = score.get('system', {}).get('processor_model', '').lower()
                    platform = score.get('system', {}).get('platform', '').lower()
                    timestamp = score.get('timestamp', '').lower()
                    ops_per_second = str(score.get('ops_per_second', '')).lower()
                    
                    # Search across all relevant fields
                    if (search_lower in cpu_model or
                        search_lower in platform or
                        search_lower in timestamp or
                        search_lower in ops_per_second):
                        filtered_scores.append(score)
            else:
                # If no search term, show all scores
                filtered_scores = self.original_all_scores
            
            # Update the table with filtered data
            self.filtered_scores = filtered_scores
            self.current_data = filtered_scores
            self._update_table_with_all_scores(filtered_scores)
            
            # Re-enable pagination controls
            self._set_pagination_controls_enabled(True)

            # Hide loading indicator after filtering
            self.query_one("#loading_display", Static).display = False
            self.query_one("#all_scores_table", DataTable).display = True
        except Exception as e:
            logging.error(f"Error during search filtering: {e}")
            # Show error message if filtering fails
            self.query_one("#loading_display", Static).update("[red]Error filtering results[/red]")
            self.query_one("#loading_display", Static).display = True
            self.query_one("#all_scores_table", DataTable).display = False

    async def _load_all_data_worker(self):
       """Worker function for loading all scores."""
       try:
           # Fetch all data from core
           all_scores = _get_all_valid_scores()
           
           # Sort by ops_per_second descending (highest first)
           all_scores.sort(key=lambda x: x.get('ops_per_second', 0), reverse=True)
           
           # Store original scores for filtering
           self.original_all_scores = all_scores
           self.current_data = all_scores
           
           # Update the UI on the main thread using post_message
           self.post_message(DataLoadComplete(all_scores))
       except Exception as e:
           logging.error(f"Error loading all scores: {e}")
           self.post_message(DataLoadError())

    def on_data_load_complete(self, message: DataLoadComplete) -> None:
        """Handle successful data loading."""
        self._update_table_with_all_scores(message.data)
    
    def on_data_load_error(self, message: DataLoadError) -> None:
        """Handle data loading error."""
        self._show_error_message()

    def _update_table_with_all_scores(self, all_scores):
        """Update table with loaded scores."""
        # Store the current page and total count for pagination
        self.current_page = 1
        self.total_items = len(all_scores)
        self.filtered_scores = all_scores
        self.current_data = all_scores # Update for export compatibility
        
        # Set input value
        try:
            self.query_one("#page_input", Input).value = str(self.current_page)
        except Exception:
            pass

        # Calculate total pages
        self._calculate_pages()
        
        # Show pagination info
        self._update_pagination_display()
        
        # Display first page
        self._display_current_page()

    def _display_current_page(self):
        """Display the current page of data."""
        try:
            table = self.query_one("#all_scores_table", DataTable)
        except Exception:
            # If we can't find the table, return early (for test environments)
            return
        
        # Clear existing data
        table.clear()
        
        # Add columns if they don't exist
        if not table.columns:
            # Add columns with appropriate widths for better display of long CPU names
            table.add_column("Rank", key="rank", width=5)
            table.add_column("CPU Model", key="cpu_model")  # No fixed width to allow dynamic sizing
            table.add_column("Platform", key="platform", width=12)
            table.add_column("Threads", key="num_threads", width=8)
            table.add_column("Ops/Second", key="ops_per_second", width=15)
            table.add_column("Timestamp", key="timestamp", width=20)  # Limit timestamp width
        
        # Calculate page boundaries
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.filtered_scores))
        
        # Add rows with rank indicators for current page only
        for i in range(start_idx, end_idx):
            score = self.filtered_scores[i]
            rank = i + 1
            cpu_model = score.get('system', {}).get('processor_model', 'N/A')
            platform = score.get('system', {}).get('platform', 'N/A')
            num_threads = str(score.get('num_threads', 1))
            ops_per_second = score.get('ops_per_second', 0)
            timestamp = score.get('timestamp', 'N/A')
            
            # Format the ops_per_second value
            formatted_ops = format_large_number(ops_per_second)
            
            # Apply rank styling
            if rank == 1:
                rank_text = f"[gold-rank]#{rank}[/gold-rank]"
            elif rank == 2:
                rank_text = f"[silver-rank]#{rank}[/silver-rank]"
            elif rank == 3:
                rank_text = f"[bronze-rank]#{rank}[/bronze-rank]"
            else:
                rank_text = f"[dark-blue-rank]#{rank}[/dark-blue-rank]"
            
            table.add_row(
                rank_text,
                cpu_model,
                platform,
                num_threads,
                formatted_ops,
                timestamp
            )
        
        # Set column widths based on content after adding rows
        self._adjust_column_widths_and_wrap_names(table)
        
        # Update pagination button states
        self._update_pagination_button_states()

        # Hide loading indicator and show table
        self.query_one("#loading_display", Static).display = False
        self.query_one("#all_scores_table", DataTable).display = True

    def _update_pagination_display(self):
        """Update the pagination display text."""
        if hasattr(self, 'total_items') and self.total_items > 0:
            start_idx = (self.current_page - 1) * self.page_size + 1
            end_idx = min(self.current_page * self.page_size, self.total_items)
            pagination_text = f"Showing {start_idx}-{end_idx} of {self.total_items} (Page {self.current_page}/{self.total_pages})"
            self.query_one("#pagination_display", Static).update(pagination_text)
        else:
            self.query_one("#pagination_display", Static).update("No results to display")
        self.query_one("#pagination_display", Static).display = True

    def _calculate_pages(self):
        """Calculate total number of pages based on total items and page size."""
        if self.page_size <= 0:
            self.total_pages = 1
        elif self.total_items == 0:
            self.total_pages = 1
        else:
            self.total_pages = (self.total_items + self.page_size - 1) // self.page_size
        # Ensure current_page is within valid range
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages if self.total_pages > 0 else 1

    def _update_pagination_button_states(self):
        """Update the state of pagination buttons based on current page."""
        try:
            # Get button widgets
            first_btn = self.query_one("#first_page", Button)
            prev_btn = self.query_one("#previous_page", Button)
            next_btn = self.query_one("#next_page", Button)
            last_btn = self.query_one("#last_page", Button)
            
            # Update button states
            first_btn.disabled = (self.current_page <= 1)
            prev_btn.disabled = (self.current_page <= 1)
            next_btn.disabled = (self.current_page >= self.total_pages)
            last_btn.disabled = (self.current_page >= self.total_pages)
            
        except Exception:
            # Skip if buttons aren't available (e.g., in test environments)
            pass

    def action_first_page(self) -> None:
        """Navigate to first page."""
        self._go_to_first_page()
    
    def action_previous_page(self) -> None:
        """Navigate to previous page."""
        self._go_to_previous_page()
    
    def action_next_page(self) -> None:
        """Navigate to next page."""
        self._go_to_next_page()
    
    def action_last_page(self) -> None:
        """Navigate to last page."""
        self._go_to_last_page()
    
    def action_goto_page(self) -> None:
        """Navigate to specific page."""
        try:
            page_input = self.query_one("#page_input", Input)
            page_num = int(page_input.value)
            if 1 <= page_num <= self.total_pages:
                self._go_to_page(page_num)
            else:
                # Show error message temporarily
                original_text = self.query_one("#pagination_display", Static).render()
                self.query_one("#pagination_display", Static).update(f"[red]Invalid page. Enter 1-{self.total_pages}[/red]")
                
                # Reset after delay
                def reset_display():
                    self.query_one("#pagination_display", Static).update(original_text)
                self.set_timer(2.0, reset_display)
        except ValueError:
            pass

    def _go_to_next_page(self):
        """Navigate to the next page."""
        if hasattr(self, 'total_items') and self.total_items > 0:
            if self.current_page < self.total_pages:
                self.current_page += 1
                self.query_one("#page_input", Input).value = str(self.current_page)
                self._display_current_page()
                self._update_pagination_display()

    def _go_to_previous_page(self):
        """Navigate to the previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self.query_one("#page_input", Input).value = str(self.current_page)
            self._display_current_page()
            self._update_pagination_display()

    def _go_to_first_page(self):
        """Navigate to the first page."""
        if self.current_page != 1:
            self.current_page = 1
            self.query_one("#page_input", Input).value = str(self.current_page)
            self._display_current_page()
            self._update_pagination_display()

    def _go_to_last_page(self):
        """Navigate to the last page."""
        if hasattr(self, 'total_items') and self.total_items > 0:
            if self.current_page != self.total_pages:
                self.current_page = self.total_pages
                self.query_one("#page_input", Input).value = str(self.current_page)
                self._display_current_page()
                self._update_pagination_display()

    def _go_to_page(self, page_num):
        """Navigate to a specific page number."""
        self.current_page = page_num
        self.query_one("#page_input", Input).value = str(self.current_page)
        self._display_current_page()
        self._update_pagination_display()

    def _adjust_column_widths_and_wrap_names(self, table):
        """Adjust column widths based on content to prevent overflow and wrap/truncate long CPU names."""
        # Get column keys directly from the dictionary keys
        column_keys = list(table.columns.keys())
        
        # Store column labels for headers based on known column keys
        column_labels = {}
        for key in column_keys:
            if str(key) == "rank":
                column_labels[key] = "Rank"
            elif str(key) == "cpu_model":
                column_labels[key] = "CPU Model"
            elif str(key) == "platform":
                column_labels[key] = "Platform"
            elif str(key) == "num_threads":
                column_labels[key] = "Threads"
            elif str(key) == "ops_per_second":
                column_labels[key] = "Ops/Second"
            elif str(key) == "timestamp":
                column_labels[key] = "Timestamp"
        
        # Get the maximum width needed for each column
        max_widths = {}
        
        # Initialize with header widths
        for key in column_keys:
            max_widths[key] = len(str(column_labels.get(key, str(key))))
        
        # Check row data for maximum width
        for row in table.rows:
            for key in table.columns.keys():
                cell_value = table.get_cell(row, key)
                if key not in max_widths:
                    max_widths[key] = 0
                current_width = len(str(cell_value))
                max_widths[key] = max(max_widths[key], current_width)
        
        # Adjust column widths (with reasonable limits)
        for column in table.columns.values():
            if column.key == "cpu_model":
                # For CPU model names, we want to allow more space but not too much
                new_width = min(max_widths[column.key], 60)  # Limit to 60 chars max for better readability
                column.width = new_width
            elif column.key == "timestamp":
                # Timestamps should be limited to prevent overflow
                new_width = min(max_widths[column.key], 25)
                column.width = new_width
            else:
                # For other columns, use reasonable limits
                if column.key == "rank":
                    column.width = 5
                elif column.key == "platform":
                    column.width = min(max_widths[column.key], 15)
                elif column.key == "num_threads":
                    column.width = 8
                elif column.key == "ops_per_second":
                    column.width = min(max_widths[column.key], 20)
        
        # Apply text wrapping for CPU model column if needed
        # Note: Textual DataTable doesn't support native text wrapping,
        # but we can truncate long names with ellipsis
        self._wrap_long_cpu_names(table)

    def _wrap_long_cpu_names(self, table):
        """Wrap or truncate long CPU model names to prevent overflow."""
        # Check if any CPU model name is too long and needs truncation
        for row in table.rows:
            cpu_model_value = table.get_cell(row, "cpu_model")
            if len(str(cpu_model_value)) > 60:  # Truncate if longer than 60 chars (matching new max width)
                truncated_name = str(cpu_model_value)[:57] + "..."
                table.set_cell(row, "cpu_model", truncated_name)

    def _show_error_message(self):
        """Show error message if data loading fails."""
        self.query_one("#loading_display", Static).update("[red]Error loading scores. Please try again.[/red]")
        self.query_one("#loading_display", Static).display = True
        self.query_one("#all_scores_table", DataTable).display = False

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "export_csv":
            # Pass filtered_scores (full dataset) instead of just current page
            self.export_data(self.filtered_scores, self.query_one("#all_scores_table", DataTable), "csv", "all_scores")
            event.stop()
        elif event.button.id == "export_json":
            # Pass filtered_scores (full dataset) instead of just current page
            self.export_data(self.filtered_scores, self.query_one("#all_scores_table", DataTable), "json", "all_scores")
            event.stop()
        elif event.button.id == "back_to_main_menu":
            self.action_go_back()
            event.stop()
        elif event.button.id == "first_page":
            self._go_to_first_page()
            event.stop()
        elif event.button.id == "previous_page":
            self._go_to_previous_page()
            event.stop()
        elif event.button.id == "next_page":
            self._go_to_next_page()
            event.stop()
        elif event.button.id == "last_page":
            self._go_to_last_page()
            event.stop()
        elif event.button.id == "goto_page":
            self.action_goto_page()
            event.stop()
        elif event.button.id == "quit_app":
            self.app.exit()
            event.stop()


class AnalyticsScreen(Screen):
    BINDINGS = [
        ("b", "go_back", "Back to Main Menu"),
        ("q", "quit_app", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Container():
            yield WowFactorHeader(id="app-header")
            yield Static(colorize_text_gradient("ANALYTICS DASHBOARD", RETRO_GRADIENT_COLORS), classes="title compact-header")
            
            with TabbedContent(classes="analytics-container"):
                with TabPane("Average by CPU"):
                    yield PlotextPlot(id="cpu_avg_plot")
                with TabPane("Score Distribution"):
                    yield PlotextPlot(id="score_dist_plot")
            
            with Horizontal(classes="action-buttons compact-button"):
                yield Button("Back", id="back_to_main_menu", variant="default")

    def on_mount(self) -> None:
        self.query_one("#app-header", WowFactorHeader).update_title("ANALYTICS")
        self.load_data()

    def load_data(self) -> None:
        self.run_worker(self._load_data_worker(), thread=True, group="data_loading")

    async def _load_data_worker(self):
        try:
            all_scores = _get_all_valid_scores()
            self.post_message(DataLoadComplete(all_scores))
        except Exception as e:
            logging.error(f"Error loading analytics data: {e}")
            self.post_message(DataLoadError())

    def on_data_load_complete(self, message: DataLoadComplete) -> None:
        self.all_scores = message.data
        self.render_charts()

    def on_data_load_error(self, message: DataLoadError) -> None:
         self.query_one("#app-header", WowFactorHeader).update_title("ANALYTICS - ERROR LOADING DATA")

    def render_charts(self) -> None:
        # CPU Average Plot
        cpu_plot = self.query_one("#cpu_avg_plot", PlotextPlot)
        cpu_plot.plt.clear_data()
        
        if hasattr(self, 'all_scores') and self.all_scores:
            cpu_models, avg_scores = aggregate_scores_by_cpu(self.all_scores)
            if cpu_models:
                cpu_plot.plt.bar(cpu_models, avg_scores)
                cpu_plot.plt.title("Average Score by CPU")
                cpu_plot.plt.xlabel("CPU Model")
                cpu_plot.plt.ylabel("Score")
            else:
                cpu_plot.plt.title("No Data Available")
        else:
             cpu_plot.plt.title("No Data Available")

        # Score Distribution Plot
        dist_plot = self.query_one("#score_dist_plot", PlotextPlot)
        dist_plot.plt.clear_data()
        
        if hasattr(self, 'all_scores') and self.all_scores:
            bins, counts = get_score_distribution(self.all_scores)
            if bins:
                dist_plot.plt.bar(bins, counts)
                dist_plot.plt.title("Score Distribution")
                dist_plot.plt.xlabel("Score Range")
                dist_plot.plt.ylabel("Count")
            else:
                dist_plot.plt.title("No Data Available")
        else:
            dist_plot.plt.title("No Data Available")
            
        # Refresh widgets
        cpu_plot.refresh()
        dist_plot.refresh()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back_to_main_menu":
            self.action_go_back()
            event.stop()
        elif event.button.id == "quit_app":
            self.app.exit()
            event.stop()


class ClearInvalidScoresConfirmationScreen(Screen):
    """Confirmation screen for clearing invalid scores."""
    
    BINDINGS = [
        ("y", "confirm", "Confirm"),
        ("n", "cancel", "Cancel"),
        ("q", "quit_app", "Quit"),
    ]
    
    def __init__(self, invalid_files_count: int):
        super().__init__()
        self.invalid_files_count = invalid_files_count
    
    def compose(self) -> ComposeResult:
        with Container(classes="main-menu-container"):
            yield WowFactorHeader(id="app-header")
            yield Static(f"Confirm: Delete {self.invalid_files_count} invalid score files?")
            yield Static("This action cannot be undone.")
            with Horizontal(classes="action-buttons"):
                yield Button("Yes, Delete", id="confirm", variant="error")
                yield Button("No, Cancel", id="cancel", variant="default")
                yield Button("Back", id="back_to_main_menu", variant="default")
    
    def on_mount(self) -> None:
        self.query_one("#app-header", WowFactorHeader).update_title("CONFIRM DELETE")
    
    def action_confirm(self) -> None:
        """Handle confirmation of deletion."""
        # Call the cleanup function from core_logic
        deleted_files = cleanup_invalid_scores()
        
        # Show results
        self.app.push_screen(ClearInvalidScoresResultScreen(len(deleted_files)))
    
    def action_cancel(self) -> None:
        """Handle cancellation of deletion."""
        self.app.pop_screen()
    
    def action_quit_app(self) -> None:
        """Handle quit action."""
        self.app.exit()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            self.action_confirm()
            event.stop()
        elif event.button.id == "cancel":
            self.action_cancel()
            event.stop()
        elif event.button.id == "back_to_main_menu":
            self.app.pop_screen()
            event.stop()
        elif event.button.id == "quit_app":
            self.action_quit_app()
            event.stop()


class ClearInvalidScoresResultScreen(Screen):
    """Screen showing results of clearing invalid scores."""
    
    BINDINGS = [
        ("b", "go_back", "Back to Main Menu"),
        ("q", "quit_app", "Quit"),
    ]
    
    def __init__(self, deleted_count: int):
        super().__init__()
        self.deleted_count = deleted_count
    
    def compose(self) -> ComposeResult:
        with Container(classes="main-menu-container"):
            yield WowFactorHeader(id="app-header")
            if self.deleted_count > 0:
                yield Static(f"Successfully deleted {self.deleted_count} invalid score files.")
            else:
                yield Static("No invalid score files found to delete.")
            with Horizontal(classes="action-buttons"):
                yield Button("Back", id="back_to_main_menu", variant="default")
    
    def on_mount(self) -> None:
        self.query_one("#app-header", WowFactorHeader).update_title("DELETE COMPLETE")
    
    def action_go_back(self) -> None:
        """Go back to main menu."""
        self.app.pop_screen()
    
    def action_quit_app(self) -> None:
        """Handle quit action."""
        self.app.exit()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back_to_main_menu":
            self.action_go_back()
            event.stop()
        elif event.button.id == "quit_app":
            self.action_quit_app()
            event.stop()


class WowFactorTUI(App):
    CSS = CLI_STYLESHEET + """
PlotextPlot {
    height: 100%;
    width: 100%;
    min-height: 20;
}
"""
    SCREENS = {
        "main_menu": MainMenuScreen,
        "run_single_benchmark": RunSingleBenchmarkScreen,
        "run_batch_benchmark": RunBatchBenchmarkScreen,
        "view_best_scores": ViewBestScoresScreen,
        "compare_cpu": CompareCPUScreen,
        "view_all_scores": ViewAllScoresScreen,
        "analytics": AnalyticsScreen,
        "clear_invalid_confirm": ClearInvalidScoresConfirmationScreen,
        "clear_invalid_result": ClearInvalidScoresResultScreen,
    }

    def on_mount(self) -> None:
        self.push_screen("main_menu")