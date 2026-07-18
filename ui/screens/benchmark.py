import asyncio
import logging
import multiprocessing
from textual.widgets import Button, Static, Input, ProgressBar, DataTable, Footer
from textual.containers import Container, VerticalScroll, Horizontal
from textual.worker import WorkerCancelled

# Import shared components to avoid circular imports
from ui.shared import WowFactorHeader, RETRO_GRADIENT_COLORS, colorize_text_gradient

# Import core benchmark functions
from core.benchmark import execute_single_benchmark_run, format_large_number

# Import validation layer
from core.validation import Validation

# Import message classes
from ui.messages import BenchmarkProgress, BenchmarkCompletion, BatchBenchmarkProgress, BatchBenchmarkCompletion, CooldownMessage

from .base_screen import BaseScreen

_validation = Validation()


class RunSingleBenchmarkScreen(BaseScreen):
    BINDINGS = [
        ("b", "go_back", "Back to Main Menu"),
        ("q", "quit_app", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="run-benchmark-screen"):
            yield WowFactorHeader(id="app-header")
            yield Static(colorize_text_gradient("RUN NEW BENCHMARK", RETRO_GRADIENT_COLORS), classes="title")
            yield Static("Enter test duration in seconds (minimum 1):", classes="form-label")
            yield Input(value="15", placeholder="Duration (seconds)", id="duration_input", type="integer", classes="form-input")
            yield Static("", id="duration_error", classes="validation-error")
            yield Static(f"Number of Threads (Max: {multiprocessing.cpu_count()}):", classes="form-label")
            yield Input(value="1", placeholder="Threads", id="threads_input", type="integer", classes="form-input")
            yield Static("", id="threads_error", classes="validation-error")
            with Horizontal(classes="action-buttons"):
                yield Button("Start", id="start_benchmark", variant="primary", classes="action-btn")
                yield Button("Stop", id="stop_benchmark", variant="error", disabled=True, classes="action-btn")
            yield Static("Progress: Ready to start...", id="progress_display")
            yield ProgressBar(id="benchmark_progress", show_eta=True)
            yield Static("", id="result_summary_display", classes="result-summary")
            yield DataTable(id="result_table", zebra_stripes=True)
            with Horizontal(classes="action-buttons"):
                yield Button("Back", id="back_to_main_menu", variant="default", classes="action-btn")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#app-header", WowFactorHeader).update_title("BENCHMARK")
        self.query_one("#stop_benchmark", Button).display = False
        self.query_one("#result_summary_display", Static).display = False
        self.query_one("#benchmark_progress", ProgressBar).display = False
        self.query_one("#result_table", DataTable).display = False
        self._benchmark_duration = 0  # Track duration for progress bar

    def _show_inline_error(self, widget_id: str, message: str) -> None:
        self.query_one(f"#{widget_id}", Static).update(f"[red]{message}[/red]")
        self.query_one(f"#{widget_id}", Static).display = True

    def _clear_inline_error(self, widget_id: str) -> None:
        self.query_one(f"#{widget_id}", Static).update("")
        self.query_one(f"#{widget_id}", Static).display = False

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

        # Clear any previous inline errors
        self._clear_inline_error("duration_error")
        self._clear_inline_error("threads_error")

        # Validate duration
        duration, dur_err = _validation.validate_duration(duration_str)
        if dur_err:
            self._show_inline_error("duration_error", dur_err)
            return

        # Validate threads
        num_threads, thr_err = _validation.validate_threads(threads_str)
        if thr_err:
            self._show_inline_error("threads_error", thr_err)
            return

        is_infinite = False

        # Track duration for meaningful progress bar
        self._benchmark_duration = duration
        self._benchmark_is_infinite = is_infinite

        self.query_one("#start_benchmark", Button).disabled = True
        self.query_one("#stop_benchmark", Button).disabled = False
        self.query_one("#stop_benchmark", Button).display = True
        self.query_one("#back_to_main_menu", Button).disabled = True
        self.query_one("#result_summary_display", Static).display = False
        self.query_one("#result_table", DataTable).display = False
        self.query_one("#progress_display", Static).update("Benchmark started...")
        self.query_one("#benchmark_progress", ProgressBar).display = True

        # Set progress bar mode: indeterminate for infinite, time-based for finite
        pb = self.query_one("#benchmark_progress", ProgressBar)
        if is_infinite:
            pb.update(total=1, completed=0)  # Indeterminate: no ETA
            pb.show_eta = False
        else:
            pb.update(total=duration, completed=0)
            pb.show_eta = True

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
                self.post_message(BenchmarkProgress(total_ops, ops_per_second, elapsed_time))

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
        self.query_one("#progress_display", Static).update(
            f"Progress: [green]Ops: {format_large_number(message.total_ops)}[/green] "
            f"| [yellow]Ops/sec: {format_large_number(message.ops_per_second)}[/yellow]"
        )
        try:
            pb = self.query_one("#benchmark_progress", ProgressBar)
            if getattr(self, '_benchmark_is_infinite', False):
                # Indeterminate: just animate with no ETA
                pb.show_eta = False
            else:
                # Time-based progress using elapsed vs total duration
                duration = getattr(self, '_benchmark_duration', 0)
                if duration > 0:
                    pb.update(total=duration, completed=min(message.elapsed_time, duration))
                    pb.show_eta = True
            pb.display = True
        except Exception:
            pass

    def on_benchmark_completion(self, message: BenchmarkCompletion) -> None:
        result_data = message.result_data
        status_message = "Benchmark completed!"
        if message.interrupted:
            status_message = "[orange_red1]Benchmark stopped prematurely![/orange_red1]"
            if "message" in result_data:
                status_message += f"\n[red]{result_data['message']}[/red]"
            elif "error" in result_data:
                error_type = result_data.get('error_type', 'Unknown')
                error_msg = result_data.get('error', '')
                status_message += f"\nError: [red]{error_type}: {error_msg}[/red]"

        if message.interrupted:
            self.navigation.notify("Benchmark stopped prematurely!", type="warning")
        else:
            self.navigation.notify("Benchmark completed successfully!", type="success")

        if not message.interrupted:
            self.navigation.notify(
                f"Benchmark complete: {format_large_number(message.result_data.get('ops_per_second', 0))} ops/sec",
                type="SUCCESS"
            )
        self.query_one("#start_benchmark", Button).disabled = False
        self.query_one("#stop_benchmark", Button).disabled = True
        self.query_one("#stop_benchmark", Button).display = False
        self.query_one("#back_to_main_menu", Button).disabled = False
        try:
            self.query_one("#benchmark_progress", ProgressBar).display = False
        except Exception:
            pass

        if "total_operations" in result_data and not message.interrupted:
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
            if message.interrupted and "message" not in result_data:
                summary_text = "[red]Benchmark was interrupted or failed to produce complete results.[/red]"

        self.query_one("#result_summary_display", Static).update(summary_text)
        self.query_one("#result_summary_display", Static).display = True

        # Populate structured DataTable with key metrics (replaces raw JSON Markdown)
        table = self.query_one("#result_table", DataTable)
        table.clear()
        table.add_columns("Metric", "Value")
        if result_data and "total_operations" in result_data and not message.interrupted:
            sys_info = result_data.get("system", {})
            rows = [
                ("Total Operations", format_large_number(result_data["total_operations"])),
                ("Ops/Second", format_large_number(result_data["ops_per_second"])),
                ("Duration", f"{result_data['duration_seconds']:.2f}s"),
                ("Threads", str(result_data.get("num_threads", 1))),
                ("CPU Model", sys_info.get("processor_model", "N/A")),
                ("CPU Freq", sys_info.get("processor_frequency", "N/A")),
                ("Platform", sys_info.get("platform", "N/A")),
                ("Results File", result_data.get("file_path", "N/A")),
            ]
            for label, value in rows:
                table.add_row(label, value)
        else:
            table.add_row("Status", "[red]No valid results[/red]")
        table.display = True


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
            yield Static("", id="batch_runs_error", classes="validation-error")
            yield Static("Number of threads (default: 1):", classes="form-label")
            yield Input(value="1", placeholder="Number of threads", id="num_threads_input", type="integer", classes="form-input")
            yield Static("", id="num_threads_error", classes="validation-error")
            yield Static("Duration for each run in seconds (minimum 1):", classes="form-label")
            yield Input(value="15", placeholder="Duration (seconds)", id="duration_input", type="integer", classes="form-input")
            yield Static("", id="batch_duration_error", classes="validation-error")
            with Horizontal(classes="action-buttons"):
                yield Button("Start Batch", id="start_batch_benchmark", variant="primary", classes="action-btn")
                yield Button("Stop Batch", id="stop_batch_benchmark", variant="error", disabled=True, classes="action-btn")
            yield Static("Current Batch: Ready to start...", id="batch_number_display")
            yield Static("Progress: Ready for run 1...", id="progress_display")
            yield ProgressBar(id="batch_progress", show_eta=True)
            yield Static("", id="cooldown_display")
            yield Static("", id="batch_summary_display", classes="result-summary")
            yield DataTable(id="batch_result_table", zebra_stripes=True)
            with Horizontal(classes="action-buttons"):
                yield Button("Back", id="back_to_main_menu", variant="default", classes="action-btn")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#app-header", WowFactorHeader).update_title("BATCH BENCHMARK")
        self.query_one("#stop_batch_benchmark", Button).display = False
        self.query_one("#batch_summary_display", Static).display = False
        self.query_one("#batch_result_table", DataTable).display = False
        self.query_one("#cooldown_display", Static).display = False
        self.query_one("#batch_progress", ProgressBar).display = False
        self._total_batch_runs = 0  # Track total for progress bar

    def _show_inline_error(self, widget_id: str, message: str) -> None:
        self.query_one(f"#{widget_id}", Static).update(f"[red]{message}[/red]")
        self.query_one(f"#{widget_id}", Static).display = True

    def _clear_inline_error(self, widget_id: str) -> None:
        self.query_one(f"#{widget_id}", Static).update("")
        self.query_one(f"#{widget_id}", Static).display = False

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

        # Clear any previous inline errors
        self._clear_inline_error("batch_runs_error")
        self._clear_inline_error("num_threads_error")
        self._clear_inline_error("batch_duration_error")

        # Validate batch runs
        num_batch_runs, runs_err = _validation.validate_batch_runs(batch_runs_input.value)
        if runs_err:
            self._show_inline_error("batch_runs_error", runs_err)
            return

        # Validate duration per run
        duration_per_run, dur_err = _validation.validate_duration(duration_input.value)
        if dur_err:
            self._show_inline_error("batch_duration_error", dur_err)
            return

        # Validate thread count
        num_threads_input = self.query_one("#num_threads_input", Input)
        num_threads, thr_err = _validation.validate_threads(num_threads_input.value)
        if thr_err:
            self._show_inline_error("num_threads_error", thr_err)
            return

        self.query_one("#start_batch_benchmark", Button).disabled = True
        self.query_one("#stop_batch_benchmark", Button).disabled = False
        self.query_one("#stop_batch_benchmark", Button).display = True
        self.query_one("#back_to_main_menu", Button).disabled = True
        self.query_one("#batch_summary_display", Static).display = False
        self.query_one("#batch_result_table", DataTable).display = False
        self.query_one("#cooldown_display", Static).display = False

        self._total_batch_runs = num_batch_runs

        self.query_one("#batch_number_display", Static).update(f"Current Batch: Starting {num_batch_runs} runs...")
        self.query_one("#progress_display", Static).update("Progress: Initializing...")
        pb = self.query_one("#batch_progress", ProgressBar)
        pb.update(total=num_batch_runs, completed=0)
        pb.show_eta = True
        pb.display = True

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
                        await asyncio.sleep(1)  # Non-blocking sleep in async worker
                    
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
        # Update progress bar with actual batch run count
        try:
            pb = self.query_one("#batch_progress", ProgressBar)
            total_runs = getattr(self, '_total_batch_runs', message.total_batch_runs)
            pb.update(total=total_runs, completed=message.batch_run_number - 1)
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

        # Populate structured DataTable with batch results (replaces raw JSON Markdown)
        table = self.query_one("#batch_result_table", DataTable)
        table.clear()
        table.add_columns("Run", "Ops/Second", "Total Ops", "Duration")
        if message.results:
            for i, rd in enumerate(message.results):
                table.add_row(
                    str(i + 1),
                    format_large_number(rd.get("ops_per_second", 0)),
                    format_large_number(rd.get("total_operations", 0)),
                    f"{rd.get('duration_seconds', 0):.2f}s",
                )
        else:
            table.add_row("N/A", "N/A", "N/A", "N/A")
        table.display = True
