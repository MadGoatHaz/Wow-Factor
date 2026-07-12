# WowFactor TUI — Screen Action Map

> Generated: 2026-07-12
> Scope: Full deep-dive of every screen, its action paths, data flows, dependencies, and crash points.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Screen Registry](#2-screen-registry)
3. [Screen-by-Screen Action Maps](#3-screen-by-screen-action-maps)
4. [Cross-Screen Dependencies](#4-cross-screen-dependencies)
5. [Data Loading Flows](#5-data-loading-flows)
6. [Crash Point Analysis](#6-crash-point-analysis)
7. [Automated Testing Recommendations](#7-automated-testing-recommendations)

---

## 1. Architecture Overview

```
wowfactor.py (launcher)
  └── ui/app.py::WowFactorTUI (Textual App)
        ├── NavigationManager (singleton, initialized on_mount)
        ├── SCREENS dict (12 registered screen names)
        └── DataExportMixin (CSV/JSON/XML/YAML export methods)
              │
              ├── MainMenuScreen (entry point, 11 buttons)
              ├── RunSingleBenchmarkScreen
              ├── RunBatchBenchmarkScreen
              ├── ViewBestScoresScreen
              ├── ViewAllScoresScreen
              ├── CompareCPUScreen
              ├── AnalyticsScreen
              ├── TrendsChartScreen
              ├── ClearInvalidScoresConfirmationScreen
              ├── ClearInvalidScoresResultScreen
              ├── ProfileSelectionScreen
              └── LoadingOverlay
```

### Key Patterns

- **Navigation**: All screens use `self.navigation` property (lazy-loaded `NavigationManager` singleton). Screens **do not** import each other; navigation is string-based via `SCREENS` dict.
- **Base Classes**: `BaseScreen` (from `base_screen.py`) = `ScreenWithServices` mixin + `TextualScreen`. Provides `services` (→ `core._registry`) and `navigation` properties. Most screens extend `Screen` directly, not `BaseScreen`.
- **Messages**: Custom Textual messages defined in `ui/messages.py` for worker→screen communication.
- **Workers**: Single benchmark uses `thread=True` worker; batch benchmark uses async worker on main event loop. Analytics/Trends use `thread=True` workers.
- **Export**: `DataExportMixin` in `ui/app.py` provides `export_data()`. XML/YAML also via `core/exporters.py`.

---

## 2. Screen Registry

All 12 entries in `WowFactorTUI.SCREENS`:

| Screen Key | Class | File | Has Custom `__init__` Args? |
|---|---|---|---|
| `main_menu` | `MainMenuScreen` | `ui/screens/main_menu.py` | No |
| `run_single_benchmark` | `RunSingleBenchmarkScreen` | `ui/screens/benchmark.py` | No |
| `run_batch_benchmark` | `RunBatchBenchmarkScreen` | `ui/screens/benchmark.py` | No |
| `view_best_scores` | `ViewBestScoresScreen` | `ui/screens/views/rendering.py` | No |
| `compare_cpu` | `CompareCPUScreen` | `ui/screens/views/charts.py` | No |
| `view_all_scores` | `ViewAllScoresScreen` | `ui/screens/views/navigation.py` | No |
| `analytics` | `AnalyticsScreen` | `ui/screens/analytics.py` | No |
| `trends_chart` | `TrendsChartScreen` | `ui/screens/analytics.py` | No |
| `clear_invalid_confirm` | `ClearInvalidScoresConfirmationScreen` | `ui/shared.py` | Yes: `invalid_count: int` |
| `clear_invalid_result` | `ClearInvalidScoresResultScreen` | `ui/screens/cleanup.py` | Yes: `deleted_count: int` |
| `profile_selection` | `ProfileSelectionScreen` | `ui/screens/profile_selection.py` | Yes: `profiles: List[str]`, `create_new: bool` |
| `loading_overlay` | `LoadingOverlay` | `ui/shared.py` | Yes: `message: str`, `dim_opacity: float` |

---

## 3. Screen-by-Screen Action Maps

### 3.1 MainMenuScreen

**File**: `ui/screens/main_menu.py` (115 lines)

**Inherits**: `textual.screen.Screen`

#### compose() Widgets
| Widget | ID | Purpose |
|---|---|---|
| `WowFactorHeader` | `app-header` | Title bar |
| `Button` | `run_single_benchmark` | Navigate to single benchmark |
| `Button` | `run_batch_benchmark` | Navigate to batch benchmark |
| `Button` | `view_best_scores` | Navigate to best scores |
| `Button` | `compare_cpu` | Navigate to CPU comparison |
| `Button` | `view_all_scores` | Navigate to all scores |
| `Button` | `view_analytics` | Navigate to analytics |
| `Button` | `view_trends` | Navigate to trends chart |
| `Button` | `clear_invalid_confirm` | Show invalid score confirmation |
| `Button` | `manage_profiles` | Navigate to profile selection |
| `Button` | `quit_app` | Quit application |
| `Static` | `command_prompt` | Status text |

#### on_mount()
- Queries `#app-header`, calls `update_title("BENCHMARK INTERFACE")`

#### Key Bindings
| Key | Action | Method |
|---|---|---|
| `q` | `quit_app` | `action_quit_app()` → `self.app.exit()` |

#### Button Handlers (on_button_pressed)
| Button ID | Action | Destination / Effect |
|---|---|---|
| `quit_app` | `action_quit_app()` | `self.app.exit()` |
| `run_single_benchmark` | `navigation.navigate_to("run_single_benchmark")` | Pushes `RunSingleBenchmarkScreen` |
| `run_batch_benchmark` | `navigation.navigate_to("run_batch_benchmark")` | Pushes `RunBatchBenchmarkScreen` |
| `view_best_scores` | `navigation.navigate_to("view_best_scores")` | Pushes `ViewBestScoresScreen` |
| `view_all_scores` | `navigation.navigate_to("view_all_scores")` | Pushes `ViewAllScoresScreen` |
| `clear_invalid_confirm` | **Inline file scan** → `navigation.navigate_to("clear_invalid_confirm", invalid_count=N)` | Scans `BENCHMARK_DIR` for invalid JSONs |
| `manage_profiles` | Loads profiles from `config_manager` → `navigation.navigate_to("profile_selection", ...)` | Pushes `ProfileSelectionScreen` |
| `compare_cpu` | `navigation.navigate_to("compare_cpu")` | Pushes `CompareCPUScreen` |
| `view_analytics` | `navigation.navigate_to("analytics")` | Pushes `AnalyticsScreen` |
| `view_trends` | `navigation.navigate_to("trends_chart")` | Pushes `TrendsChartScreen` |
| *(default/else)* | `navigation.notify(...)` | Shows notification toast |

#### Data Flows
- **Clear Invalid Count**: Reads `BENCHMARK_DIR` files directly using `os.listdir` + `json.load` — **synchronous I/O on UI thread**.
- **Profile Loading**: `config_manager.get_all_profiles()` → profile names list.

---

### 3.2 RunSingleBenchmarkScreen

**File**: `ui/screens/benchmark.py` (lines 1–243)

**Inherits**: `textual.screen.Screen`

#### compose() Widgets
| Widget | ID | Purpose |
|---|---|---|
| `WowFactorHeader` | `app-header` | Title bar |
| `Static` | *(title)* | "RUN NEW BENCHMARK" |
| `Input` | `duration_input` | Test duration in seconds |
| `Input` | `threads_input` | Number of threads |
| `Button` | `start_benchmark` | Start benchmark |
| `Button` | `stop_benchmark` | Stop benchmark (initially hidden) |
| `Static` | `progress_display` | Live progress updates |
| `Static` | `result_summary_display` | Result summary (initially hidden) |
| `Markdown` | `result_markdown_display` | JSON dump of result (initially hidden) |
| `Button` | `back_to_main_menu` | Go back |

#### on_mount()
- Updates header title to "BENCHMARK"
- Hides `stop_benchmark`, `result_summary_display`, `result_markdown_display`

#### Key Bindings
| Key | Action | Method |
|---|---|---|
| `b` | `go_back` | `self.navigation.go_back()` |
| `q` | `quit_app` | `self.app.exit()` |

#### Button Handlers
| Button ID | Method | Effect |
|---|---|---|
| `start_benchmark` | `start_benchmark_run()` | Validates inputs, shows loading overlay, spawns worker |
| `stop_benchmark` | `stop_benchmark_run()` | Cancels `benchmark_worker` |
| `back_to_main_menu` | `action_go_back()` | `navigation.go_back()` |
| `quit_app` | *(inline)* | `self.app.exit()` |

#### Worker
- `benchmark_worker = self.run_worker(lambda: self._benchmark_worker_function(...), thread=True, group="benchmark_workers")`
- Worker calls `execute_single_benchmark_run()` from `core/benchmark.py`
- Posts `BenchmarkProgress` and `BenchmarkCompletion` messages

#### Message Handlers
| Message | Handler | Effect |
|---|---|---|
| `BenchmarkProgress` | `on_benchmark_progress()` | Updates `#progress_display` widget |
| `BenchmarkCompletion` | `on_benchmark_completion()` | Dismisses loading overlay, shows results summary + markdown |

#### Data Flow
```
User clicks Start
  → start_benchmark_run() validates inputs
  → navigation.navigate_to("loading_overlay", message="Running benchmark...")
  → run_worker(thread=True) → _benchmark_worker_function()
      → execute_single_benchmark_run() (core/benchmark.py)
          → creates threads, runs CPU workload
          → save_benchmark_results() → writes JSON to BENCHMARK_DIR
          → invalidates cache
      → post_message(BenchmarkProgress) each 50ms
      → post_message(BenchmarkCompletion) on finish
  → on_benchmark_completion() → go_back() (dismisses overlay)
  → updates result_summary_display + result_markdown_display
```

#### Notifications
- `"Benchmark stopped prematurely!"` (warning) on interruption
- `"Benchmark completed successfully!"` (success) on normal completion
- `f"Benchmark complete: {ops/sec} ops/sec"` (SUCCESS — **note: uppercase key**)

---

### 3.3 RunBatchBenchmarkScreen

**File**: `ui/screens/benchmark.py` (lines 245–498)

**Inherits**: `textual.screen.Screen`

#### compose() Widgets
| Widget | ID | Purpose |
|---|---|---|
| `WowFactorHeader` | `app-header` | Title bar |
| `Input` | `batch_runs_input` | Number of batch runs (2–100) |
| `Input` | `num_threads_input` | Number of threads |
| `Input` | `duration_input` | Duration per run |
| `Button` | `start_batch_benchmark` | Start batch |
| `Button` | `stop_batch_benchmark` | Stop batch (hidden initially) |
| `Static` | `batch_number_display` | Current batch run number |
| `Static` | `progress_display` | Live progress |
| `Static` | `cooldown_display` | Cooldown countdown (hidden initially) |
| `Static` | `batch_summary_display` | Summary (hidden initially) |
| `Markdown` | `batch_markdown_display` | JSON dump (hidden initially) |
| `Button` | `back_to_main_menu` | Go back |

#### on_mount()
- Sets header title to "BATCH BENCHMARK"
- Hides stop, summary, markdown, cooldown displays

#### Key Bindings
| Key | Action | Method |
|---|---|---|
| `b` | `go_back` | `self.navigation.go_back()` |
| `q` | `quit_app` | `self.app.exit()` |

#### Button Handlers
| Button ID | Method | Effect |
|---|---|---|
| `start_batch_benchmark` | `start_batch_benchmark()` | Validates inputs, spawns async worker |
| `stop_batch_benchmark` | `stop_batch_benchmark()` | Cancels `batch_worker_instance` |
| `back_to_main_menu` | `action_go_back()` | `navigation.go_back()` |
| `quit_app` | *(inline)* | `self.app.exit()` |

#### Worker
- `batch_worker_instance = self.run_worker(lambda: self._batch_benchmark_worker_function(...), group="batch_benchmark_workers")` — **async, runs on main event loop**
- Loops `num_batch_runs` times, calling `execute_single_benchmark_run()` for each
- 5-second cooldown between runs (`time.sleep(1)` in worker thread is safe since it's async in main loop context)

#### Message Handlers
| Message | Handler | Effect |
|---|---|---|
| `BatchBenchmarkProgress` | `on_batch_benchmark_progress()` | Updates batch number + progress display |
| `CooldownMessage` | `on_cooldown_message()` | Shows cooldown countdown |
| `BatchBenchmarkCompletion` | `on_batch_benchmark_completion()` | Shows summary + markdown, re-enables buttons |

#### Notifications
- `"Batch interrupted. Not all runs completed."` (warning)
- `"Batch benchmark complete!"` (success)
- `f"Batch complete: {avg_ops} ops/sec average"` (SUCCESS — **note: uppercase key**)

---

### 3.4 ViewBestScoresScreen

**File**: `ui/screens/views/rendering.py` (240 lines)

**Inherits**: `textual.screen.Screen`

#### compose() Widgets
| Widget | ID | Purpose |
|---|---|---|
| `WowFactorHeader` | `app-header` | Title bar |
| `Static` | `search_label` | "Search:" label |
| `Input` | `search_input` | Search filter input |
| `Static` | `loading_display` | Loading indicator |
| `DataTable` | `best_scores_table` | Ranked score table |
| `Button` | `export_csv` | Export to CSV |
| `Button` | `export_json` | Export to JSON |
| `Button` | `export_xml` | Export to XML |
| `Button` | `export_yaml` | Export to YAML |
| `Button` | `back_to_main_menu` | Go back |

#### on_mount()
- Sets header title to "BEST SCORES"
- Resets `current_data = []`
- Calls `load_data()`

#### Key Bindings
| Key | Action | Method |
|---|---|---|
| `b` | `go_back` | `self.navigation.go_back()` |
| `q` | `quit_app` | `self.app.exit()` |

#### Button Handlers
| Button ID | Method | Effect |
|---|---|---|
| `export_csv` | `export_data(current_data, table, "csv", "best_scores")` | From `DataExportMixin` |
| `export_json` | `export_data(current_data, None, "json", "best_scores")` | From `DataExportMixin` |
| `export_xml` | `XmlExporter.export(...)` | Direct core exporter |
| `export_yaml` | `YamlExporter.export(...)` | Direct core exporter |
| `back_to_main_menu` | `action_go_back()` | `navigation.go_back()` |
| `quit_app` | *(inline)* | `self.app.exit()` |

#### Input Handlers
| Event | Handler | Effect |
|---|---|---|
| `Input.Submitted` | `on_input_submitted()` → `_filter_scores()` | Filters `original_all_scores` by search term |

#### Data Loading Flow
```
on_mount() → load_data()
  → navigation.navigate_to("loading_overlay", "Loading best scores...")
  → get_best_score_per_machine() (core/benchmark.py)
      → _get_all_valid_scores() (cached)
      → group by (processor_model, platform)
      → select best ops_per_second per group
  → navigation.go_back() (dismiss overlay)
  → _update_table_with_scores(scores)
      → DataTable.add_column(), add_row()
      → LayoutOptimizer.calculate_column_widths()
      → hide loading_display
```

#### Notifications
- `"Error loading scores. Please try again."` (error) on data load failure

---

### 3.5 ViewAllScoresScreen

**File**: `ui/screens/views/navigation.py` (361 lines)

**Inherits**: `textual.screen.Screen`

#### compose() Widgets
| Widget | ID | Purpose |
|---|---|---|
| `WowFactorHeader` | `app-header` | Title bar |
| `Static` | `search_label` | "Search:" label |
| `Input` | `search_input` | Search filter |
| `Static` | `loading_display` | Loading indicator |
| `DataTable` | `all_scores_table` | Paginated score table |
| `Static` | `pagination_info` | Page info text |
| `Button` | `first_page` | First page |
| `Button` | `previous_page` | Previous page |
| `Button` | `next_page` | Next page |
| `Button` | `last_page` | Last page |
| `Button` | `export_csv` | Export CSV |
| `Button` | `export_json` | Export JSON |
| `Button` | `back_to_main_menu` | Go back |

#### on_mount()
- Sets header title to "ALL SCORES"
- Initializes pagination state: `current_page=1, page_size=50, total_pages=1, total_items=0`
- Calls `load_data()`

#### Key Bindings
| Key | Action | Method |
|---|---|---|
| `b` | `go_back` | `self.navigation.go_back()` |
| `q` | `quit_app` | `self.app.exit()` |
| `pageup` | `previous_page` | `action_previous_page()` |
| `pagedown` | `next_page` | `action_next_page()` |
| `home` | `first_page` | `action_first_page()` |
| `end` | `last_page` | `action_last_page()` |
| `g` | `goto_page` | `action_goto_page()` — notifies "needs implementation" |

#### Button Handlers
| Button ID | Effect |
|---|---|
| `export_csv` | `export_data(filtered_scores, table, "csv", "all_scores")` |
| `export_json` | `export_data(filtered_scores, None, "json", "all_scores")` |
| `back_to_main_menu` | `navigation.go_back()` |
| `quit_app` | `self.app.exit()` |

**NOTE**: Button IDs `first_page`, `previous_page`, `next_page`, `last_page` are defined in compose but **NOT handled in `on_button_pressed`**. They are only triggered by key bindings. Buttons exist but clicking them does nothing.

#### Input Handlers
| Event | Handler | Effect |
|---|---|---|
| `Input.Submitted` | `on_input_submitted()` → `_filter_scores()` | Filters `original_all_scores`, recalculates pagination |

#### Data Loading Flow
```
on_mount() → load_data()
  → navigation.navigate_to("loading_overlay", "Loading all scores...")
  → _get_all_valid_scores() (core/benchmark.py, cached)
  → navigation.go_back()
  → sorted by timestamp desc → original_all_scores
  → _calculate_pages() → total_pages
  → _update_table() (page 1)
```

#### Notifications
- `"Showing page {N} of {M}"` (info) — **called on every page change**
- `"Error loading CPU scores. Please try again."` (error)
- `"Page navigation via 'g' key requires additional UI"` (via `self.notify()`)

---

### 3.6 CompareCPUScreen

**File**: `ui/screens/views/charts.py` (227 lines)

**Inherits**: `textual.screen.Screen`

#### compose() Widgets
| Widget | ID | Purpose |
|---|---|---|
| `WowFactorHeader` | `app-header` | Title bar |
| `Static` | `first_cpu_label` | "Select First CPU:" label |
| `Input` | `first_cpu_input` | First CPU model text input |
| `Static` | `second_cpu_label` | "Select Second CPU:" label |
| `Input` | `second_cpu_input` | Second CPU model text input |
| `Button` | `compare_button` | Execute comparison |
| `Static` | `loading_display` | Loading indicator |
| `DataTable` | `comparison_table` | Comparison results table |
| `Button` | `back_to_main_menu` | Go back |

#### on_mount()
- Sets header title to "CPU COMPARISON"
- Initializes `available_cpus = []`
- Calls `load_available_cpus()` (synchronous, **not in worker**)

#### Key Bindings
| Key | Action | Method |
|---|---|---|
| `b` | `go_back` | `self.navigation.go_back()` |
| `q` | `quit_app` | `self.app.exit()` |

#### Button Handlers
| Button ID | Effect |
|---|---|
| `compare_button` | Reads inputs, validates non-empty, calls `get_scores_for_cpu()` for both, stores in `self.cpu1_data` / `self.cpu2_data`, calls `_display_comparison()` |
| `back_to_main_menu` | `navigation.go_back()` |
| `quit_app` | `self.app.exit()` |

#### Data Flow
```
on_mount() → load_available_cpus() (SYNC, blocks UI)
  → _get_all_valid_scores()
  → extracts unique CPU models → available_cpus (stored but never displayed!)

User clicks Compare
  → get_scores_for_cpu(cpu1) + get_scores_for_cpu(cpu2)
  → _display_comparison()
      → clears table, adds columns
      → calculates avg/max/Number of Runs
      → populates table with formatted numbers
```

#### Notifications
- `"Error loading CPUs."` (error)
- `"Please enter both CPU models"` (warning)

---

### 3.7 AnalyticsScreen

**File**: `ui/screens/analytics.py` (lines 200–544)

**Inherits**: `BaseScreen` (from `base_screen.py`)

#### compose() Widgets
| Widget | ID | Purpose |
|---|---|---|
| `WowFactorHeader` | `app-header` | Title bar |
| `TabbedContent` | `analytics-container` | Tab container |
| `PlotextPlot` | `cpu_avg_plot` | Bar chart: avg score by CPU |
| `PlotextPlot` | `score_dist_plot` | Bar chart: score distribution |
| `PlotextPlot` | `threads_scatter_plot` | Scatter: threads vs score |
| `PlotextPlot` | `freq_scatter_plot` | Scatter: frequency vs score |
| `Static` | `cpu_stats_cards` | Statistics cards per CPU |
| `Static` | `trend_sparklines` | Sparkline trends |
| `Button` | `back_to_main_menu` | Go back |
| `Button` | `generate_report` | Generate analytics report |

#### on_mount()
- Sets header title to "ANALYTICS"
- Calls `load_data()`

#### Key Bindings
| Key | Action | Method |
|---|---|---|
| `b` | `go_back` | `self.navigation.go_back()` (inherited from BaseScreen pattern) |
| `q` | `quit_app` | `self.app.exit()` |

#### Button Handlers
| Button ID | Method | Effect |
|---|---|---|
| `back_to_main_menu` | `action_go_back()` | `navigation.go_back()` |
| `generate_report` | `_generate_analytics_report()` | Creates `AnalyticsEngine`, generates report, saves JSON to CWD |
| `quit_app` | *(inline)* | `self.app.exit()` |

#### Tab Change Handler
| Tab | Triggered Method |
|---|---|
| "Correlations" | `_render_scatter_plots()` |
| "Summary & Trends" | `_render_summary_and_trends()` |

#### Worker
- `self.run_worker(lambda: self._load_data_worker(), thread=True, group="data_loading")`
- Loads `_get_all_valid_scores()`, posts `DataLoadComplete` or `DataLoadError`

#### Message Handlers
| Message | Handler | Effect |
|---|---|---|
| `DataLoadComplete` | `on_data_load_complete()` | Stores `self.all_scores`, calls `render_charts()` |
| `DataLoadError` | `on_data_load_error()` | Shows error notification |

#### Data Flow
```
on_mount() → load_data() → worker(_load_data_worker)
  → _get_all_valid_scores()
  → post_message(DataLoadComplete)
→ on_data_load_complete() → render_charts()
  → cpu_avg_plot: aggregate_scores_by_cpu()
  → score_dist_plot: get_score_distribution()
  → plots refresh

Tab change to "Correlations" → _render_scatter_plots()
  → extracts threads+score pairs, freq+score pairs
  → linear regression for trend lines
  → renders scatter plots

Tab change to "Summary & Trends" → _render_summary_and_trends()
  → AnalyticsEngine().get_stats_per_cpu_model()
  → engine.get_scores_by_cpu_model()
  → engine.detect_trends(), engine.get_trend_visualization()
  → renders stats cards + sparklines
```

#### Notifications
- `"Error loading analytics data. Please try again."` (error)
- `"No benchmark data available for reporting"` (error)
- `"Analytics report saved to {filename}"` (success)
- `"Error saving report: {e}"` (error)

#### File I/O
- **Report export**: Writes `analytics_report_{timestamp}.json` to **current working directory**

---

### 3.8 TrendsChartScreen

**File**: `ui/screens/analytics.py` (lines 57–198)

**Inherits**: `BaseScreen`

#### compose() Widgets
| Widget | ID | Purpose |
|---|---|---|
| `WowFactorHeader` | `app-header` | Title bar |
| `TabbedContent` | `analytics-container` | Tab container |
| `PlotextPlot` | `all_cpus_plot` | Line chart: all scores over time |
| `PlotextPlot` | `cpu_specific_plot` | Placeholder for per-CPU tabs |
| `Button` | `back_to_main_menu` | Go back |

#### on_mount()
- Sets header title to "TRENDS CHART"
- Calls `load_data()`

#### Key Bindings
| Key | Action | Method |
|---|---|---|
| `b` | `go_back` | `self.navigation.go_back()` |
| `q` | `quit_app` | `self.app.exit()` |

#### Button Handlers
| Button ID | Effect |
|---|---|
| `back_to_main_menu` | `navigation.go_back()` |
| `quit_app` | `self.app.exit()` |

#### Worker
- `self.run_worker(lambda: self._load_data_worker(), thread=True, group="data_loading")`

#### Message Handlers
| Message | Handler | Effect |
|---|---|---|
| `DataLoadComplete` | `on_data_load_complete()` | Stores `self.all_scores`, calls `render_charts()` |
| `DataLoadError` | `on_data_load_error()` | Shows error notification |

#### Data Flow
```
load_data() → worker → _get_all_valid_scores() → DataLoadComplete
→ render_charts()
  → groups scores by CPU model
  → sorts each group by timestamp
  → converts timestamps to Unix epoch
  → renders combined line chart on all_cpus_plot
  → _update_cpu_tabs():
      removes placeholder tab
      adds dynamic TabPane per CPU model (but individual CPU plots are never rendered!)
```

**CRITICAL BUG**: `_update_cpu_tabs()` creates new `PlotextPlot` widgets dynamically but never renders data on them. The individual CPU tabs are empty.

#### Notifications
- `"Error loading trends data. Please try again."` (error)

---

### 3.9 ClearInvalidScoresConfirmationScreen

**File**: `ui/shared.py` (lines 68–116)

**Inherits**: `textual.screen.Screen`

#### `__init__` Parameters
- `invalid_count: int = 0`

#### compose() Widgets
| Widget | ID | Purpose |
|---|---|---|
| `WowFactorHeader` | `app-header` | Title bar |
| `Static` | `info_display` | Shows count of invalid files |
| `Static` | `confirm_message` | "Are you sure..." prompt |
| `Button` | `confirm_clear` | Confirm deletion |
| `Button` | `cancel_clear` | Cancel |

#### on_mount()
- Sets header title to "CLEAR INVALID SCORES CONFIRMATION"

#### Key Bindings
| Key | Action | Method |
|---|---|---|
| `y` | `confirm_clear` | Posts `ClearInvalidScoresConfirmed`, pops screen |
| `n` | `cancel_clear` | Pops screen |
| `q` | `quit_app` | `self.app.exit()` |

#### Button Handlers
| Button ID | Effect |
|---|---|
| `confirm_clear` | `action_confirm_clear()` → posts `ClearInvalidScoresConfirmed(invalid_count)`, pops screen |
| `cancel_clear` | `action_cancel_clear()` → pops screen |

**CRITICAL**: `ClearInvalidScoresConfirmed` message is posted but **no parent screen listens for it**. The `MainMenuScreen` navigates to this screen but never handles the confirmation message. The actual deletion is **never executed** after user confirms.

---

### 3.10 ClearInvalidScoresResultScreen

**File**: `ui/screens/cleanup.py` (60 lines)

**Inherits**: `textual.screen.Screen`

#### `__init__` Parameters
- `deleted_count: int`

#### compose() Widgets
| Widget | ID | Purpose |
|---|---|---|
| `WowFactorHeader` | `app-header` | Title bar |
| `Static` | `status-display` | Shows deletion result |
| `Button` | `back_to_main_menu` | Go back |

#### Key Bindings
| Key | Action | Method |
|---|---|---|
| `b` | `go_back` | `navigation.go_back()` |
| `q` | `quit_app` | `self.app.exit()` |

**NOTE**: This screen is registered in `SCREENS` as `clear_invalid_result` but is **never navigated to** by any existing code path. The confirmation screen doesn't navigate here after deletion.

---

### 3.11 ProfileSelectionScreen

**File**: `ui/screens/profile_selection.py` (53 lines)

**Inherits**: `textual.screen.Screen`

#### `__init__` Parameters
- `profiles: List[str]`
- `create_new: bool = False`

#### compose() Widgets
| Widget | ID | Purpose |
|---|---|---|
| `Label` | `profile-title` | "Select a Benchmark Profile" |
| `Button` | `create_new_profile` | Create new profile |
| `Button` | `select_{name}` | Select existing profile |
| `Button` | `cancel_selection` | Cancel |

#### Button Handlers
| Button ID | Effect |
|---|---|
| `create_new_profile` | `self.app.notify("Profile creation not yet implemented")` |
| `select_{name}` | `self.app.notify(f"Selected profile: {name}")` → `self.navigation.go_back()` |
| `cancel_selection` | `self.navigation.go_back()` |

**CRITICAL**: Both "Create New Profile" and "Select" are **placeholders**. Profile creation is stubbed out. Profile selection just shows a notification and goes back — it doesn't actually apply the profile to benchmark settings.

---

### 3.12 LoadingOverlay

**File**: `ui/shared.py` (lines 118–145)

**Inherits**: `textual.screen.Screen`

#### `__init__` Parameters
- `message: str = "Loading..."`
- `dim_opacity: float = 0.7`

#### compose() Widgets
| Widget | ID | Purpose |
|---|---|---|
| `Container` | `loading-overlay` | Full-screen overlay container |
| `Static` | `loading-text` | Loading message text |

#### Key Bindings
| Key | Action | Method |
|---|---|---|
| `escape` | `dismiss` | `self.dismiss()` (pops screen) |

**NOTE**: No `on_button_pressed` handler. Only dismissible via `escape` key or programmatic `go_back()`.

---

### 3.13 WowFactorHeader (Shared Widget)

**File**: `ui/shared.py` (lines 52–65)

**Inherits**: `textual.widgets.Static`

#### Methods
| Method | Effect |
|---|---|
| `update_title(new_title)` | Renders gradient header text with title |

---

## 4. Cross-Screen Dependencies

### NavigationManager (ui/navigation.py)

```
NavigationManager (singleton)
  ├── initialize(app) — stores _app reference
  ├── navigate_to(screen_name, **kwargs)
  │     → looks up self.app.SCREENS[screen_name]
  │     → instantiates screen_class(**kwargs)
  │     → self.app.push_screen(screen_instance)
  ├── go_back()
  │     → if screen_stack > 1: self.app.pop_screen()
  ├── reset_to_main()
  │     → pops until main_menu, ensures active
  └── notify(message, type)
        → ToastNotification.show(parent=screen, ...)
```

### DataExportMixin (ui/app.py)

Mixed into `WowFactorTUI` — screens call `self.export_data()` which:
1. CSV: reads DataTable columns/rows, strips markup, writes CSV
2. JSON: dumps raw data dict list
3. XML/YAML: delegates to `core.exporters`

**NOTE**: Mixin calls `self.query_one("#loading_display", ...)` — screens must have a `#loading_display` widget for export feedback.

### Message Class Hierarchy (ui/messages.py)

```
BenchmarkProgress(total_ops, ops_per_second)
BenchmarkCompletion(result_data, interrupted)
BatchBenchmarkProgress(batch_run_number, total_batch_runs, total_ops, ops_per_second)
BatchBenchmarkCompletion(results, total_batch_runs, interrupted)
CooldownMessage(current_batch_run, total_batch_runs, cooldown_seconds)
DataLoadComplete(data)
DataLoadError()
```

### Service Registry Gap

`ScreenWithServices.services` tries to `from core import _registry`. **`core/__init__.py` does NOT export `_registry`**. This property would always raise `ImportError` if accessed. No screen currently accesses `.services` — only `.navigation` is used.

---

## 5. Data Loading Flows

### 5.1 _get_all_valid_scores() (core/benchmark.py)

```
_get_all_valid_scores():
  1. Check _cache (OrderedDict, TTL 300s)
  2. If cache miss:
     a. os.listdir(BENCHMARK_DIR) for *.json files
     b. For each file: json.load() → validate required fields
        (ops_per_second, system, system.processor_model)
     c. Cache result
  3. Return list[dict]
```

**Called by**: ViewBestScoresScreen, ViewAllScoresScreen, CompareCPUScreen, AnalyticsScreen, TrendsChartScreen, AnalyticsEngine

### 5.2 get_best_score_per_machine() (core/benchmark.py)

```
get_best_score_per_machine():
  1. Check _cache
  2. _get_all_valid_scores()
  3. Group by (processor_model, platform)
  4. Select max ops_per_second per group
  5. Sort desc by ops_per_second
  6. Cache result
```

**Called by**: ViewBestScoresScreen

### 5.3 get_scores_for_cpu() (core/benchmark.py)

```
get_scores_for_cpu(cpu_model_name):
  1. Check _cache per CPU
  2. _get_all_valid_scores()
  3. Filter by system.processor_model == cpu_model_name
  4. Cache result
```

**Called by**: CompareCPUScreen

### 5.4 aggregate_scores_by_cpu() / get_score_distribution() (core/benchmark.py)

Pure computation functions, no file I/O. Used by AnalyticsScreen for chart data.

---

## 6. Crash Point Analysis

### 6.1 CRITICAL — High Probability Crashes

| # | Location | Trigger | Crash Type | Root Cause |
|---|---|---|---|---|
| **C1** | `ui/screens/base_screen.py:38` | Any screen inheriting `BaseScreen` calls `.services` | `ImportError` | `from core import _registry` — `_registry` is **never defined** in `core/__init__.py`. AnalyticsScreen and TrendsChartScreen inherit from `BaseScreen`. |
| **C2** | `ui/screens/profile_selection.py:48,52` | Clicking any profile button | `AttributeError` | `self.navigation` is never defined. `ProfileSelectionScreen` inherits from raw `Screen`, not `BaseScreen`, and has no `_navigation` property or `navigation` property. |
| **C3** | `ui/app.py:41,64-68,72-77` | Export CSV/JSON from any screen without `#loading_display` widget | `NoMatches` | `DataExportMixin.export_data()` calls `self.query_one("#loading_display", Static)`. Many screens (e.g., CompareCPUScreen) don't have this widget. |
| **C4** | `ui/screens/views/rendering.py:227-238` | Search on ViewBestScoresScreen | `AttributeError` | `_filter_scores()` references `self.original_all_scores` which is **never set**. Only `self.current_data` is set in `_update_table_with_scores()`. Search will always return empty results or crash. |
| **C5** | `ui/screens/views/charts.py:88-89` | ViewBestScoresScreen load | `AttributeError` / `UnboundLocalError` | `load_available_cpus()` tries to set `self.available_cpus` but this is CompareCPUScreen, not ViewBestScoresScreen — this method is in CompareCPUScreen and calls `self.query_one("#loading_display")` which may not exist depending on state. |
| **C6** | `ui/shared.py:101-102` | Confirm clear invalid scores | **Logic death** | `ClearInvalidScoresConfirmed` message is posted but never handled. The actual `cleanup_invalid_scores()` from `core/benchmark.py` is **never called**. The confirmation screen pops but deletion never happens. |
| **C7** | `ui/screens/analytics.py:166-184` | View any per-CPU trend tab | **Empty chart** | `_update_cpu_tabs()` adds `PlotextPlot` widgets dynamically but never populates them with data. Individual CPU trend tabs show blank plots. |

### 6.2 HIGH — Likely Crashes Under Certain Conditions

| # | Location | Trigger | Crash Type | Root Cause |
|---|---|---|---|---|
| **H1** | `ui/screens/main_menu.py:53` | Screen mount without `#app-header` | `NoMatches` | `query_one("#app-header", WowFactorHeader)` — if header fails to compose. Unlikely but possible under Textual version changes. |
| **H2** | `ui/navigation.py:52-53` | `navigate_to()` with unknown screen name | `ValueError` | Raises explicit error. The `SCRE`ENS dict lookup is guarded but any typo in navigation calls crashes. |
| **H3** | `ui/navigation.py:76-77` | `reset_to_main()` | `TypeError` | `self.app.push_screen("main_menu")` passes a string — but `push_screen()` expects a screen instance or class. The first branch pops screens, but this `push_screen("main_menu")` call will fail. |
| **H4** | `ui/screens/benchmark.py:111` | Start benchmark | `RuntimeError` (if LoadingOverlay fails) | `navigation.navigate_to("loading_overlay", ...)` — if the overlay screen fails to push, subsequent widget queries still execute. |
| **H5** | `ui/screens/benchmark.py:186` | Benchmark completion handler | `RuntimeError` | `self.navigation.go_back()` dismisses loading overlay. If overlay was already dismissed (e.g., via escape key), `go_back()` pops the benchmark screen itself. |
| **H6** | `ui/screens/views/navigation.py:316-317` | Export CSV/JSON from ViewAllScoresScreen | `AttributeError` | `export_data()` called but `DataExportMixin` is only on `WowFactorTUI`, not on `ViewAllScoresScreen`. The method **does not exist** on this screen class. |
| **H7** | `ui/screens/views/rendering.py:191-203` | Export CSV/JSON from ViewBestScoresScreen | `AttributeError` | Same as H6: `export_data()` is a `DataExportMixin` method, not available on `ViewBestScoresScreen`. XML/YAML exports work (direct core calls), but CSV/JSON calls to `self.export_data()` will fail. |

### 6.3 MEDIUM — Crashes Under Stress

| # | Location | Trigger | Crash Type |
|---|---|---|---|
| **M1** | `ui/notifications.py:143-146` | Any notification | `AttributeError` | `parent.after(duration * 1000, ...)` — Textual's `after()` takes seconds, not milliseconds. The `* 1000` makes it dismiss after ~50 minutes instead of 3 seconds. If `schedule` fallback is used, different behavior. |
| **M2** | `ui/screens/benchmark.py:407-413` | Batch benchmark during cooldown | `WorkerCancelled` mishandling | `time.sleep(1)` in async worker blocks the main event loop. Combined with `is_cancelled` check, cancellation detection is delayed by up to 5 seconds. |
| **M3** | `core/benchmark.py:173-191` | `_get_all_valid_scores()` with corrupted JSON | Silent swallow | Invalid JSON files are silently skipped. No user notification. User won't know data is missing. |
| **M4** | `core/analytics_engine.py:137-138` | `detect_trend()` with same-timestamp data | Division by zero | `denominator == 0` check exists but `change_percent` calculation at line 191-195 has no zero-division guard on `recent_data[0][1]` — actually it does have one. Low risk. |
| **M5** | `ui/screens/analytics.py:341-347` | Frequency parsing | `ValueError` swallowed | Regex fallback to `float()` on "N/A" or empty string would fail. Caught by outer try/except but silently skipped. |
| **M6** | `ui/screens/analytics.py:516-520` | Generate report with engine | `AttributeError` | `engine._scores_cache = self.all_scores` — sets private attribute. If `AnalyticsEngine` changes internal structure, this breaks. |
| **M7** | `ui/shared.py:12` | Any screen using `Shared` | `ImportError` | `from ui.theme import ColorPalette, SpacingScale` — if theme module fails to load, ALL screens fail. |

### 6.4 LOW — Edge Cases

| # | Location | Trigger | Crash Type |
|---|---|---|---|
| **L1** | `ui/screens/benchmark.py:186` | Pressing Escape during loading overlay | `RuntimeError` | Overlay dismissed early, `on_benchmark_completion()` calls `go_back()` and pops benchmark screen |
| **L2** | `core/comparator.py:75` | `load_result()` with 128+ unique files | Cache overflow | `@lru_cache(maxsize=128)` — older results evicted, reloaded on next access |
| **L3** | `ui/screens/views/charts.py:168` | Compare with no data for a CPU | `IndexError` | `cpu1_data[0].get(...)` — if `cpu1_data` is empty list. Caught by `if not cpu1_data` check? No — the check only validates non-empty string inputs. An empty model match returns `[]`. |

---

## 7. Automated Testing Recommendations

### 7.1 Priority P0 — Must Have (Crash Prevention)

| Test | What to Verify | Tool |
|---|---|---|
| **P0-1** | `core._registry` does not exist | `ImportError` assertion on `from core import _registry` |
| **P0-2** | `ProfileSelectionScreen.navigation` attribute | Mock app, verify `self.navigation` exists or fails gracefully |
| **P0-3** | `ClearInvalidScoresConfirmed` handler | Verify message is handled somewhere or mark as dead code |
| **P0-4** | `ViewBestScoresScreen._filter_scores()` | Mock scores data, verify `original_all_scores` is populated |
| **P0-5** | `ViewAllScoresScreen.export_data()` | Verify method exists or implement it |
| **P0-6** | `ViewBestScoresScreen.export_data()` | Verify method exists or implement it |
| **P0-7** | `NavigationManager.reset_to_main()` | Mock app, verify `push_screen()` receives valid type |
| **P0-8** | `CompareCPUScreen._update_comparison_table()` | Mock empty cpu data, verify no IndexError |

### 7.2 Priority P1 — Should Have (Behavioral Correctness)

| Test | What to Verify | Tool |
|---|---|---|
| **P1-1** | `MainMenuScreen` button → screen navigation | Textual `pytest_textual` snapshot testing |
| **P1-2** | `RunSingleBenchmarkScreen` full lifecycle | Mock `execute_single_benchmark_run`, verify message flow |
| **P1-3** | `RunBatchBenchmarkScreen` full lifecycle | Mock benchmark calls, verify batch progress messages |
| **P1-4** | `ViewBestScoresScreen` data loading + table render | Mock `_get_all_valid_scores`, verify DataTable rows |
| **P1-5** | `ViewAllScoresScreen` pagination | Mock large dataset, verify page boundaries |
| **P1-6** | `CompareCPUScreen` comparison logic | Mock `get_scores_for_cpu`, verify table metrics |
| **P1-7** | `AnalyticsScreen` chart rendering | Mock `_get_all_valid_scores`, verify PlotextPlot calls |
| **P1-8** | `TrendsChartScreen` data rendering | Mock scores, verify timestamp conversion and plot data |
| **P1-9** | `ClearInvalidScoresConfirmationScreen` confirm | Mock post_message, verify message dispatched |
| **P1-10** | `DataExportMixin` CSV/JSON export | Mock data + table, verify file output |
| **P1-11** | `NavigationManager` navigate_to/go_back | Mock app/SCREENS, verify push/pop calls |
| **P1-12** | `ToastNotification.show()` dismissal | Mock parent.after(), verify cleanup after duration |

### 7.3 Priority P2 — Nice to Have (Core Module Coverage)

| Test | What to Verify | Tool |
|---|---|---|
| **P2-1** | `execute_single_benchmark_run()` | Integration test with short duration (1s) |
| **P2-2** | `save_benchmark_results()` file I/O | Temp directory, verify JSON written and cached |
| **P2-3** | `get_best_score_per_machine()` ranking | Mock scores, verify sorting and grouping |
| **P2-4** | `cleanup_invalid_scores()` | Create invalid JSON files, verify deletion |
| **P2-5** | `AnalyticsEngine.get_stats_per_cpu_model()` | Mock scores, verify statistical calculations |
| **P2-6** | `AnalyticsEngine.detect_trends()` | Mock scores with known trend, verify direction |
| **P2-7** | `XmlExporter` / `YamlExporter` / `CsvExporter` | Mock data, verify file content |
| **P2-8** | `ConfigManager` CRUD | Mock filesystem, verify profile create/read/update/delete |
| **P2-9** | `LayoutOptimizer.calculate_column_widths()` | Mock data, verify width calculations |
| **P2-10** | `cache` TTL and invalidation | Mock time, verify eviction behavior |

### 7.4 Suggested Test Infrastructure

```
tests/
  ├── conftest.py                  # Fixtures: mock_app, mock_nav, mock_benchmark_dir
  ├── test_screens/
  │   ├── test_main_menu.py        # P1-1
  │   ├── test_benchmark.py        # P1-2, P1-3
  │   ├── test_view_best_scores.py # P1-4, P0-4, P0-6
  │   ├── test_view_all_scores.py  # P1-5, P0-5
  │   ├── test_compare_cpu.py      # P1-6, P0-8
  │   ├── test_analytics.py        # P1-7, P1-8
  │   ├── test_trends.py           # P1-8
  │   ├── test_cleanup.py          # P1-9, P0-3
  │   ├── test_profile_selection.py # P0-2
  │   └── test_loading_overlay.py  # Basic compose + dismiss
  ├── test_ui/
  │   ├── test_navigation.py       # P1-11, P0-7
  │   ├── test_notifications.py    # P1-12, M1
  │   ├── test_export_mixin.py     # P1-10, H6, H7
  │   ├── test_shared.py           # WowFactorHeader, CLI_STYLESHEET
  │   └── test_base_screen.py      # P0-1
  ├── test_core/
  │   ├── test_benchmark.py        # P2-1 through P2-4
  │   ├── test_analytics_engine.py # P2-5, P2-6
  │   ├── test_exporters.py        # P2-7
  │   ├── test_config.py           # P2-8
  │   └── test_comparator.py       # L2
  └── test_layout/
      └── test_layout_utils.py     # P2-9, P2-10
```

### 7.5 Recommended pytest-textual Pattern

```python
import pytest
from pytest_textual.plugin import screen_pytest
from textual.screen import Screen

@pytest.fixture
def mock_benchmark_dir(tmp_path):
    """Create a temporary benchmark results directory."""
    results_dir = tmp_path / "benchmark_results"
    results_dir.mkdir()
    return results_dir

async def test_run_single_benchmark_lifecycle(mock_benchmark_dir):
    # Patch BENCHMARK_DIR, mock execute_single_benchmark_run
    # Use pytest-textual run_until to verify widget state changes
    async with self.run_test() as pilot:
        await pilot.click("#start_benchmark")
        # Wait for completion message
        await pilot.pause()
        result_display = screen.query_one("#result_summary_display", Static)
        assert result_display.display is True
```

---

## Appendix A: Screen Inheritance Summary

| Screen | Base Class | Has `navigation` Property | Can Access `.services` |
|---|---|---|---|
| `MainMenuScreen` | `Screen` | Yes (own `_navigation`) | No |
| `RunSingleBenchmarkScreen` | `Screen` | Yes (own `_navigation`) | No |
| `RunBatchBenchmarkScreen` | `Screen` | Yes (own `_navigation`) | No |
| `ViewBestScoresScreen` | `Screen` | Yes (own `_navigation`) | No |
| `ViewAllScoresScreen` | `Screen` | Yes (own `_navigation`) | No |
| `CompareCPUScreen` | `Screen` | Yes (own `_navigation`) | No |
| `AnalyticsScreen` | `BaseScreen` | Yes (via mixin) | **CRASH** — `_registry` missing |
| `TrendsChartScreen` | `BaseScreen` | Yes (via mixin) | **CRASH** — `_registry` missing |
| `ClearInvalidScoresConfirmationScreen` | `Screen` | No (uses `self.app.pop_screen` directly) | No |
| `ClearInvalidScoresResultScreen` | `Screen` | Yes (own `_navigation`) | No |
| `ProfileSelectionScreen` | `Screen` | **CRASH** — no `_navigation` defined | No |
| `LoadingOverlay` | `Screen` | No (uses `self.dismiss()`) | No |

## Appendix B: All Notification Calls

| Screen | Notification Type | Message Pattern |
|---|---|---|
| MainMenuScreen | info | `f"Command: {label} selected"` |
| RunSingleBenchmarkScreen | error | "Invalid duration..." |
| RunSingleBenchmarkScreen | error | "Invalid thread count..." |
| RunSingleBenchmarkScreen | warning | "Benchmark stopped prematurely!" |
| RunSingleBenchmarkScreen | success | "Benchmark completed successfully!" |
| RunSingleBenchmarkScreen | SUCCESS | `f"Benchmark complete: {ops} ops/sec"` |
| RunBatchBenchmarkScreen | error | "Invalid number of batch runs..." |
| RunBatchBenchmarkScreen | error | "Invalid duration..." |
| RunBatchBenchmarkScreen | error | "Invalid thread count..." |
| RunBatchBenchmarkScreen | warning | "Batch interrupted..." |
| RunBatchBenchmarkScreen | success | "Batch benchmark complete!" |
| RunBatchBenchmarkScreen | SUCCESS | `f"Batch complete: {avg} ops/sec average"` |
| ViewBestScoresScreen | error | "Error loading scores..." |
| ViewAllScoresScreen | error | "Error loading CPU scores..." |
| ViewAllScoresScreen | info | `f"Showing page {N} of {M}"` |
| CompareCPUScreen | error | "Error loading CPUs." |
| CompareCPUScreen | warning | "Please enter both CPU models" |
| AnalyticsScreen | error | "Error loading analytics data..." |
| AnalyticsScreen | error | "No benchmark data available..." |
| AnalyticsScreen | success | `f"Analytics report saved to {fn}"` |
| AnalyticsScreen | error | `f"Error saving report: {e}"` |
| TrendsChartScreen | error | "Error loading trends data..." |
| ViewAllScoresScreen | (self.notify) | "Page navigation via 'g' key..." |
| ProfileSelectionScreen | (self.app.notify) | "Profile creation not yet implemented" |
| ProfileSelectionScreen | (self.app.notify) | `f"Selected profile: {name}"` |

---

*End of Screen Action Map*