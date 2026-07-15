import json
import logging
import multiprocessing
import time
from textual.widgets import Button, Static, Input, Markdown, ProgressBar, Footer
from textual.containers import Container, VerticalScroll, Horizontal
from textual.worker import WorkerCancelled

# Import shared components to avoid circular imports
from ui.shared import WowFactorHeader, RETRO_GRADIENT_COLORS, colorize_text_gradient

# Import core benchmark functions
from core.benchmark import execute_single_benchmark_run, format_large_number

# Import message classes
from ui.messages import BenchmarkProgress, BenchmarkCompletion, BatchBenchmarkProgress, BatchBenchmarkCompletion, CooldownMessage

from .base_screen import BaseScreen


class RunSingleBenchmarkScreen(BaseScreen):
    BINDINGS = [
        ("b", "go_back", "Back to Main Menu"),
        ("q", "quit_app", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="run-benchmark-screen"):
            yield WowFactorHeader(id="app-header")
            yield Static(colorize_text_gradient("RUN NEW BENCHMARK", RETRO_GRADIENT_COLORS), classes="title")
            yield Static("Enter test duration in seconds (0 for infinite):", classes="form-label")
            yield Input(value="15", placeholder="Duration (seconds)", id="duration_input", type="integer", classes="form-input")
            yield Static(f"Number of Threads (Max: {multiprocessing.cpu_count()}):", classes="form-label")
            yield Input(value="1", placeholder="Threads", id="threads_input", type="integer", classes="form-input")
            with Horizontal(classes="action-buttons"):
                yield Button("Start", id="start_benchmark", variant="primary", classes="action-btn")
                yield Button("Stop", id="stop_benchmark", variant="error", disabled=True, classes="action-btn")
            yield Static("Progress: Ready to start...", id="progress_display")
            yield ProgressBar(id="benchmark_progress", show_eta=True)
            yield Static("", id="result_summary_display", classes="result-summary")
            yield Markdown("", id="result_markdown_display") # Using Markdown for flexible output
            with Horizontal(classes="action-buttons"):
                yield Button("Back", id="back_to_main_menu", variant="default", classes="action-btn")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#app-header", WowFactorHeader).update_title("BENCHMARK")
        self.query_one("#stop_benchmark", Button).display = False # Hide stop button initially
        self.query_one("#result_summary_display", Static).display = False
        self.query_one("#benchmark_progress", ProgressBar).display = False
        self.query_one("#result_markdown_display", Markdown).display = False

    def action_go_back(self) -> None:
        self.navigation.go_back()

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
            self.navigation.notify("Invalid duration. Please enter a positive integer or 0 for infinite.", type="error")
            return
            
        # Validate range: must be non-negative (positive integer or zero)
        if duration < 0:
            self.navigation.notify("Invalid duration. Please enter a positive integer or 0 for infinite.", type="error")
            return

        # Validate threads
        try:
            num_threads = int(threads_str)
        except ValueError:
            self.navigation.notify("Invalid thread count. Please enter a positive integer.", type="error")
            return
        
        if num_threads < 1:
            self.navigation.notify("Thread count must be at least 1.", type="error")
            return

        is_infinite = (duration == 0)

        # Show loading overlay during benchmark execution
        self.navigation.navigate_to("loading_overlay", message="Running benchmark...")

        self.query_one("#start_benchmark", Button).disabled = True
        self.query_one("#stop_benchmark", Button).disabled = False
        self.query_one("#stop_benchmark", Button).display = True
        self.query_one("#back_to_main_menu", Button).disabled = True
        self.query_one("#result_summary_display", Static).display = False
        self.query_one("#result_markdown_display", Markdown).display = False
        self.query_one("#progress_display", Static).update("Benchmark started...")
        self.query_one("#benchmark_progress", ProgressBar).display = True

        self.benchmark_worker = self.run_worker(
            lambda: self._benchmark_worker_function(duration, is_infinite, num_threads),
            thread=True,  # Sync function requires thread=True
            group="benchmark_workers",
        )

    def stop_benchmark_run(self) -> None:
        if hasattr(self, 'benchmark_worker') and self.benchmark_worker.is_running:
            self.benchmark_worker.cancel() # This will raise WorkerCancelled on the worker thread
            self.query_one("#progress_display", Static).update("Stopping benchmark (please wait)...")

    def _benchmark_worker_function(self, duration: float, is_infinite: bool, num_threads: int):
        total_ops = 0
        ops_per_second = 0.0
        try:
            def progress_callback(current_total_ops: int, current_time: float, start_time: float):
                # Check for cancellation
                if hasattr(self, 'benchmark_worker') and self.benchmark_worker.is_cancelled:
                    raise WorkerCancelled()

                nonlocal total_ops, ops_per_second
                total_ops = current_total_ops
                elapsed_time = current_time - start_time
                ops_per_second = total_ops / elapsed_time if elapsed_time > 0 else 0
                self.post_message(BenchmarkProgress(total_ops, ops_per_second))

            result = execute_single_benchmark_run(duration, is_infinite, num_threads, progress_callback)
            self.post_message(BenchmarkCompletion(result))
        except Exception as e:
            # Check specifically for WorkerCancelled exception from Textual
            if isinstance(e, WorkerCancelled):
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
        # Progress updates remain as direct widget updates for real-time feedback
        self.query_one("#progress_display", Static).update(
            f"Progress: [green]Ops: {format_large_number(message.total_ops)}[/green] | [yellow]Ops/sec: {format_large_number(message.ops_per_second)}[/yellow]"
        )
        # Update progress bar
        try:
            pb = self.query_one("#benchmark_progress", ProgressBar)
            pb.update(total=999999999, completed=message.total_ops)
            pb.display = True
        except Exception:
            pass

    def on_benchmark_completion(self, message: BenchmarkCompletion) -> None:
        # Dismiss the loading overlay when benchmark completes or errors
        self.navigation.go_back()
        
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

        # Show success/error notification based on benchmark result
        if message.interrupted:
            self.navigation.notify("Benchmark stopped prematurely!", type="warning")
        else:
            self.navigation.notify("Benchmark completed successfully!", type="success")
        
        # Replace direct status update with notification for completion feedback
        if not message.interrupted:
            self.navigation.notify(f"Benchmark complete: {format_large_number(message.result_data.get('ops_per_second', 0))} ops/sec", type="SUCCESS")
        self.query_one("#start_benchmark", Button).disabled = False
        self.query_one("#stop_benchmark", Button).disabled = True
        self.query_one("#stop_benchmark", Button).display = False
        self.query_one("#back_to_main_menu", Button).disabled = False
        try:
            self.query_one("#benchmark_progress", ProgressBar).display = False
        except Exception:
            pass

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


class RunBatchBenchmarkScreen(BaseScreen):
    BINDINGS = [
        ("b", "go_back", "Back to Main Menu"),
        ("q", "quit_app", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="run-benchmark-screen"):
            yield WowFactorHeader(id="app-header")
            yield Static(colorize_text_gradient("RUN BATCH BENCHMARK", RETRO_GRADIENT_COLORS), classes="title")
            yield Static("Number of batch runs (2-100):", classes="form-label")
            yield Input(value="5", placeholder="Batch Runs (2-100)", id="batch_runs_input", type="integer", classes="form-input")
            yield Static("Number of threads (default: 1):", classes="form-label")
            yield Input(value="1", placeholder="Number of threads", id="num_threads_input", type="integer", classes="form-input")
            yield Static("Duration for each run in seconds (default: 15):", classes="form-label")
            yield Input(value="15", placeholder="Duration (seconds)", id="duration_input", type="integer", classes="form-input")
            with Horizontal(classes="action-buttons"):
                yield Button("Start Batch", id="start_batch_benchmark", variant="primary", classes="action-btn")
                yield Button("Stop Batch", id="stop_batch_benchmark", variant="error", disabled=True, classes="action-btn")
            yield Static("Current Batch: Ready to start...", id="batch_number_display")
            yield Static("Progress: Ready for run 1...", id="progress_display")
            yield ProgressBar(id="batch_progress", show_eta=True)
            yield Static("", id="cooldown_display")
            yield Static("", id="batch_summary_display", classes="result-summary")
            yield Markdown("", id="batch_markdown_display")
            with Horizontal(classes="action-buttons"):
                yield Button("Back", id="back_to_main_menu", variant="default", classes="action-btn")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#app-header", WowFactorHeader).update_title("BATCH BENCHMARK")
        self.query_one("#stop_batch_benchmark", Button).display = False
        self.query_one("#batch_summary_display", Static).display = False
        self.query_one("#batch_markdown_display", Markdown).display = False
        self.query_one("#cooldown_display", Static).display = False
        self.query_one("#batch_progress", ProgressBar).display = False

    def action_go_back(self) -> None:
        self.navigation.go_back()

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
            self.navigation.notify("Invalid number of batch runs. Please enter an integer between 2 and 100.", type="error")
            return
            
        # Validate range for batch runs: must be between 2 and 100 inclusive
        if not (2 <= num_batch_runs <= 100):
            self.navigation.notify("Number of batch runs must be between 2 and 100.", type="error")
            return

        # Validate duration per run input
        try:
            duration_per_run = int(duration_input.value)
        except ValueError:
            self.navigation.notify("Invalid duration. Please enter a positive integer for duration per run.", type="error")
            return
            
        # Validate range for duration per run: must be positive (greater than 0)
        if duration_per_run <= 0:
            self.navigation.notify("Duration per run must be a positive integer.", type="error")
            return

        # Validate num_threads input
        num_threads_input = self.query_one("#num_threads_input", Input)
        try:
            num_threads = int(num_threads_input.value)
        except ValueError:
            self.navigation.notify("Invalid thread count. Please enter a positive integer.", type="error")
            return
            
        if num_threads < 1:
            self.navigation.notify("Thread count must be at least 1.", type="error")
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
        self.query_one("#batch_progress", ProgressBar).display = True

        self.batch_worker_instance = self.run_worker(
            lambda: self._batch_benchmark_worker_function(num_batch_runs, duration_per_run, num_threads),
            # thread=True removed - async functions run in main event loop
            group="batch_benchmark_workers",
        )

    def stop_batch_benchmark(self) -> None:
        if hasattr(self, 'batch_worker_instance') and self.batch_worker_instance.is_running:
            self.batch_worker_instance.cancel()
            self.query_one("#progress_display", Static).update("Stopping batch benchmark (please wait)...")

    async def _batch_benchmark_worker_function(self, num_batch_runs: int, duration_per_run: int, num_threads: int = 1, cooldown_duration: int = 5):
        all_results = []
        try:
            for i in range(1, num_batch_runs + 1):
                # Check for cancellation before starting run
                if hasattr(self, 'batch_worker_instance') and self.batch_worker_instance.is_cancelled:
                    raise WorkerCancelled()

                self.post_message(BatchBenchmarkProgress(i, num_batch_runs, 0, 0.0))
                # Removed unsafe UI update: self.query_one("#progress_display", Static).update(...)
                
                current_run_ops = 0
                current_run_ops_per_second = 0.0
                
                def progress_callback(total_ops: int, current_time: float, start_time: float):
                    # Check for cancellation during run
                    if hasattr(self, 'batch_worker_instance') and self.batch_worker_instance.is_cancelled:
                        raise WorkerCancelled()

                    nonlocal current_run_ops, current_run_ops_per_second
                    current_run_ops = total_ops
                    elapsed = current_time - start_time
                    current_run_ops_per_second = total_ops / elapsed if elapsed > 0 else 0.0
                    self.post_message(BatchBenchmarkProgress(i, num_batch_runs, current_run_ops, current_run_ops_per_second))
                
                result = execute_single_benchmark_run(duration_per_run, False, num_threads, progress_callback)
                all_results.append(result)
                
                if i < num_batch_runs:
                    for remaining_cooldown in range(cooldown_duration, 0, -1):
                        # Check for cancellation during cooldown
                        if hasattr(self, 'batch_worker_instance') and self.batch_worker_instance.is_cancelled:
                            raise WorkerCancelled()

                        self.post_message(CooldownMessage(i, num_batch_runs, remaining_cooldown))
                        time.sleep(1) # Safe to sleep in worker thread
                    
                    # Update to 0 or clear message at end of cooldown if needed,
                    # but next loop iteration will update progress immediately
        except Exception as e:
            # Check specifically for WorkerCancelled exception from Textual
            if isinstance(e, WorkerCancelled):
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
        # Update progress bar
        try:
            pb = self.query_one("#batch_progress", ProgressBar)
            pb.update(total=999999999, completed=message.total_ops)
            pb.display = True
        except Exception:
            pass

    def on_cooldown_message(self, message: CooldownMessage) -> None:
        self.query_one("#cooldown_display", Static).update(
            f"[yellow]Cooldown: {message.cooldown_seconds}s until next run (BATCH RUN {message.current_batch_run + 1} OF {message.total_batch_runs})...[/yellow]"
        )
        self.query_one("#cooldown_display", Static).display = True

    def on_batch_benchmark_completion(self, message: BatchBenchmarkCompletion) -> None:
        # Show notification based on completion status
        if message.interrupted:
            self.navigation.notify("Batch interrupted. Not all runs completed.", type="warning")
        else:
            self.navigation.notify("Batch benchmark complete!", type="success")
        
        # Replace direct status updates with notifications for batch completion feedback
        if not message.interrupted and message.results:
            avg_ops_per_second = sum(r.get('ops_per_second', 0.0) for r in message.results) / len(message.results)
            self.navigation.notify(f"Batch complete: {format_large_number(avg_ops_per_second)} ops/sec average", type="SUCCESS")
        self.query_one("#start_batch_benchmark", Button).disabled = False
        self.query_one("#stop_batch_benchmark", Button).disabled = True
        self.query_one("#stop_batch_benchmark", Button).display = False
        self.query_one("#back_to_main_menu", Button).disabled = False
        self.query_one("#cooldown_display", Static).display = False
        try:
            self.query_one("#batch_progress", ProgressBar).display = False
        except Exception:
            pass

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
