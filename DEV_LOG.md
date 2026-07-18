# DEV_LOG.md - GUI Rework Cycle
Project: WowFactor
Started: 2026-07-15
Blueprint: plans/BLUEPRINT.md

@@@ CURRENT_STATE @@@
Wave 1 complete. Wave 2 I1-I6 merged. Wave 3 I5 merged. I7 tests for system_deps.py on branch/i7. Post-merge target: 737+ total tests passed.

## Wave 1 - CP1: Unify Theme Tokens With TCSS
- [Done] Added `to_tcss_variables()` method to ColorPalette in theme.py
- [Done] Rewrote styles.tcss with Textual `$variable` syntax (no `:root`, TCSS-native)
- [Done] Replaced all hardcoded hex colors in styles.tcss rules with `$variable` references
- [Done] Deleted CLI_STYLESHEET dead code (260 lines) from shared.py
- [Done] Cleaned up unused imports (core.benchmark, SpacingScale, Dict, Any, os) from shared.py
- [Done] Fixed test_final_functionality.py test_css_styling to check for `$` variable syntax
- Tests: 535 passed, 1 failed (was :root check), 4 skipped — all green after fix
- Final: 536 passed, 0 failed, 4 skipped, 2 warnings
- Merged to master: 2026-07-15

## Wave 1 - CP2: Universal BaseScreen Adoption + Navigation Mixin
- [Done] Changed 8 screens from `Screen` to `BaseScreen` inheritance
  (main_menu, benchmark x2, cleanup, profile_selection, charts, navigation, rendering)
- [Done] Removed 8 duplicate `_navigation` property definitions (single source in base_screen.py)
- [Done] Removed 4 proxy methods from benchmark screens (`execute_single_benchmark_run`,
  `format_large_number` x2) — replaced with direct `core.benchmark` imports
- [Done] Added missing `Horizontal` import to cleanup.py (fixes P0 render crash)
- [Done] Removed unused `typing` imports (Any, Optional) from all converted screens
- [Done] Updated 3 tests to verify direct core imports instead of removed proxies
- Tests: 536 passed, 0 failed, 4 skipped, 2 warnings
- Merged to master: 2026-07-15

## Wave 1 - CP3: Extract Shared Screens to Proper Modules
- [Done] Created `ui/screens/overlay.py` with `LoadingOverlay` class — fixed CSS
  (`alignment` → `align`, removed invalid `layout: center`), reduced default
  `dim_opacity` from 0.7 to 0.4
- [Done] Created `ui/screens/confirmation.py` with `ClearInvalidScoresConfirmationScreen`
  extending `BaseScreen` (from CP2) and `ClearInvalidScoresConfirmed` message
- [Done] Removed `LoadingOverlay`, `ClearInvalidScoresConfirmationScreen`, and
  `ClearInvalidScoresConfirmed` from `ui/shared.py` (82 lines removed)
- [Done] Updated `ui/screens/__init__.py` re-exports for new modules
- [Done] Updated `ui/app.py` imports to new module paths
- [Done] Updated 3 test files: `test_app_comprehensive.py`, `comprehensive_test_suite.py`,
  `test_integration_app_startup.py` — all imports redirected to new modules
- [Done] Fixed `test_loading_overlay_default` assertion: dim_opacity 0.7 → 0.4
- shared.py now contains only `RETRO_GRADIENT_COLORS`, `colorize_text_gradient()`,
  and `WowFactorHeader` (genuinely shared utilities)
- Tests: 536 passed, 0 failed, 4 skipped, 3 warnings
- Merged to master: 2026-07-15

## Wave 1 - MERGE SUMMARY
- Fast-forward merge: master updated b7ec338..c84a87a
- 20 files changed, 309 insertions(+), 541 deletions(-)
- 2 new files: ui/screens/confirmation.py, ui/screens/overlay.py
- Post-merge test run: 536 passed, 0 failed, 4 skipped, 3 warnings
- Pushed to origin/master

## Wave 2 - I3: Replace CPU Text Input with Dropdown in CompareCPUScreen (CHUNK-I3)
- [Done] Replaced two `Input` widgets with `Select` dropdowns in CompareCPUScreen
  for CPU model selection (eliminates free-text typing errors)
- [Done] Added `_populate_select_widgets()` to populate both Select widgets from
  `available_cpus` loaded from benchmark data
- [Done] Added `_get_selected_cpu()` helper to safely read Select values,
  returning empty string for unselected (Select.NULL) state
- [Done] Updated `_display_comparison()` to show 5 metrics with better/worse
  visual differentiation using Rich markup: bold green for better value,
  dim for worse value
- [Done] Metrics expanded to: Average, Max, Min, Std Dev OPS/sec, Sample Count
  (was only 3 metrics before)
- [Done] Implemented `_calc_stats()` static method computing avg, max, min,
  population stddev, and count from benchmark score lists
- [Done] Removed dead `_update_comparison_table()` method (39 lines of code)
- [Done] Removed unused imports: `Iterable` from typing, `Key` from
  `textual.events`, `logging`
- [Done] Added CSS rules for Select widget styling (.cpu-select, .Select--overlay,
  .SelectOption, .SelectOption--highlight, .SelectOption--selected, .SelectCurrent)
  and comparison highlighting (.better, .worse)
- [Done] Updated test_integration_screen_actions.py::test_compare_cpu_validation_rejects_empty_inputs
  to use Select widget IDs (#first_cpu_select, #second_cpu_select) and Select.NULL
- [Done] Updated test_loading_states.py to check for _display_comparison instead of
  removed _update_comparison_table
- [Done] Added 29 new tests in test_i3_compare_cpu_dropdown.py covering: Select
  widget composition, CPU dropdown population, stats calculation correctness,
  dead code removal verification, better/worse highlighting logic, expanded
  metrics structure, _get_selected_cpu helper, compare_cpu method, screen inheritance
- Branch: branch/i3-settings
- Tests: 570 passed, 0 failed, 4 skipped, 3 warnings

## Wave 2 - I1: HomeScreen Rework (CHUNK-I1)
- [Done] CleanupScreen visual improvements: added `[bold green]SUCCESS[/]` and
  `[bold yellow]WARNING[/]` Rich markup messages, applied `cleanup-success` and
  `cleanup-warning` CSS classes, styled with `#status_message` id
- [Done] Title updated from "DELETE COMPLETE" to "CLEANUP COMPLETE"
- [Done] Added cleanup-specific CSS rules to styles.tcss: `.status-display` with
  padding/border/margin, `.cleanup-success` (green border), `.cleanup-warning` (yellow border)
- [Done] Removed stale `Horizontal` import workaround from
  `test_app_comprehensive.py::test_clear_invalid_result_compose`
- [Done] Added 6 new tests: `test_cleanup_screen_deleted_count`,
  `test_cleanup_screen_has_bindings`, `test_cleanup_screen_inherits_basescreen`,
  `test_cleanup_screen_imports_horizontal` (test_harness_all_paths.py),
  `test_clear_invalid_result_success_message` (test_app_comprehensive.py)
- Branch: branch/i1-home (82d560e)
- Tests: 545 passed, 0 failed, 4 skipped, 3 warnings
- Pushed to origin/branch/i1-home

## Wave 2 - I2: Fix ViewBestScoresScreen Search (CHUNK-I2)
- [Done] Fixed P0 bug: search filtering against undefined `self.original_all_scores`
- [Done] Added `self.original_all_scores = []` initialization in `__init__`
- [Done] Populated `self.original_all_scores` in `load_data()` before calling
  `_update_table_with_scores` (guards against overwrite during filter re-renders)
- [Done] Fixed `_filter_scores` to filter from `original_all_scores` and re-render
  DataTable after both filtering and clearing search
- [Done] Consolidated 4 export buttons (CSV, JSON, XML, YAML) into single "Export"
  button that pushes `ExportMenuScreen` modal overlay
- [Done] Created `ExportMenuScreen(Screen)` with 4 export format buttons,
  keyboard bindings (1-4), Escape to close, and core exporter delegation
- [Done] Removed dead `export_to_csv` method from ViewBestScoresScreen
- [Done] Cleaned up unused imports (Binding, Message, Key, logging, datetime from screen)
- [Done] Added `ExportMenuScreen` to `ui/screens/views/__init__.py` re-exports
- [Done] Updated `test_export_improvements.py`: removed `export_to_csv` calls,
  uses `core.exporters` directly, fixed working directory leak with os.chdir
- [Done] Added 27 new tests in `test_i2_search_filter.py`: initialization, filtering
  logic, case insensitivity, clear restoration, export menu structure, button consolidation
- Branch: branch/i2-runner
- Tests: 569 passed, 0 failed, 4 skipped, 2 warnings
- Pushed to origin/branch/i2-runner

## Wave 2 - I4: Fix Benchmark Progress Bars (CHUNK-I4)
- [Done] Removed `navigate_to("loading_overlay")` from RunSingleBenchmarkScreen —
  overlay blocked progress visibility during benchmark execution
- [Done] Replaced `ProgressBar(total=999999999)` fake progress with time-based
  progress for finite benchmarks (elapsed_time vs total duration) and indeterminate
  mode for infinite (duration=0) benchmarks
- [Done] Replaced `Markdown` JSON dump result display with structured `DataTable`
  showing: Total Operations, Ops/Second, Duration, Threads, CPU Model, CPU Freq,
  Platform, Results File (single benchmark) and Run, Ops/Second, Total Ops,
  Duration per run (batch benchmark)
- [Done] Added `elapsed_time` field to `BenchmarkProgress` message class with
  backward-compatible default of 0.0
- [Done] Replaced `time.sleep(1)` with `await asyncio.sleep(1)` in batch benchmark
  cooldown loop to avoid blocking the event loop
- [Done] Batch benchmark progress bar now tracks actual batch run count (Run N of M)
  instead of fake operation counter
- [Done] Removed unused imports: `json`, `time`, `Markdown`, `Container` from
  benchmark.py; added `asyncio`, `DataTable`
- [Done] Added `_benchmark_duration` and `_benchmark_is_infinite` attributes to
  track benchmark configuration for progress bar mode selection
- [Done] Updated `ui/messages.py`: `BenchmarkProgress` now accepts `elapsed_time`
  parameter
- [Done] Added 26 new tests in `test_i4_progress_bars.py`: fake total removal,
  loading overlay removal, Markdown replacement, DataTable composition, elapsed_time
  usage, async cooldown, message field, module-level checks
- Branch: branch/i4
- Tests: 624 passed, 0 failed, 4 skipped, 4 warnings

## Wave 2 - I6: Implement Profile Creation Screen (CHUNK-I6)
- [Done] Created `ui/screens/profile_creation.py` with `ProfileCreationScreen`
  extending `BaseScreen` — complete form with 5 Input fields (name, duration,
  threads, batch runs, cooldown), Save/Cancel buttons, error display
- [Done] Full input validation: name required + max 100 chars + no duplicates,
  duration 1-3600, threads 1-cpu_count, batch_runs 1-100, cooldown 0-300
- [Done] Profile persistence via `ConfigManager.create_profile()` with schema
  validation — profiles saved to `~/.config/wowfactor/benchmark_profiles.json`
- [Done] `ProfileCreatedMessage` class for cross-screen communication on save
- [Done] Keybindings: `ctrl+s` save, `b` back, `q` quit — all visible in Footer
- [Done] Updated `ProfileSelectionScreen` to wire "Create New Profile" button to
  push `ProfileCreationScreen` (replaces stub notification)
- [Done] Added `b` and `q` keybindings to `ProfileSelectionScreen`
- [Done] Removed unused `Static` import from `ProfileSelectionScreen`
- [Done] Added `_sanitize_id()` method to ProfileSelectionScreen for safe CSS
  identifiers from profile names with special characters
- [Done] Registered `ProfileCreationScreen` in `ui/app.py` SCREENS dict
- [Done] Re-exported `ProfileCreationScreen` and `ProfileCreatedMessage` from
  `ui/screens/__init__.py`
- [Done] Added TCSS styles to `styles.tcss` for profile creation form fields,
  error display, and button container
- [Done] Updated `test_app_comprehensive.py::test_app_screen_count` and
  `test_integration_app_startup.py::test_app_has_all_required_screen_types`
  to expect 13 screens (was 12)
- [Done] Added 43 new tests in `test_i6_profile_creation.py`: screen inheritance,
  bindings, widget composition, input validation (9 cases), persistence (3 cases),
  navigation (2 cases), ProfileSelectionScreen wiring (4 cases), message class,
  app registration (3 cases), TCSS styles (2 cases), import checks (3 cases)
- Branch: branch/i6
- Tests: 667 passed, 0 failed, 4 skipped, 4 warnings

## Wave 3 - I5: Add Footer Widget to All Screens (CHUNK-I5)
- [Done] Added `compose()` method to `BaseScreen` that yields `Footer()` —
  Footer auto-docks to bottom and displays keybindings from BINDINGS
- [Done] Updated 11 BaseScreen subclasses to include `yield Footer()` in their
  compose methods: MainMenuScreen, ClearInvalidScoresResultScreen,
  ProfileSelectionScreen, RunSingleBenchmarkScreen, RunBatchBenchmarkScreen,
  CompareCPUScreen, ViewBestScoresScreen, ViewAllScoresScreen,
  TrendsChartScreen, AnalyticsScreen, ClearInvalidScoresConfirmationScreen
- [Done] Footer placed OUTSIDE main Container blocks so it auto-docks correctly
  at screen bottom without layout conflicts
- [Done] Modal overlays excluded from Footer: LoadingOverlay (extends Screen,
  not BaseScreen), ExportMenuScreen (extends Screen, modal dialog)
- [Done] Added Footer CSS styling to styles.tcss: background uses $bg-darker,
  color uses $text-muted (theme tokens from CP1)
- [Done] Added 53 new tests in test_i5_footer.py covering: BaseScreen compose,
  Footer presence in all 11 screens, Footer imports, CSS styling with theme tokens,
  BINDINGS existence on all screens, BaseScreen inheritance verification,
  modal overlay exclusion (no Footer in LoadingOverlay/ExportMenuScreen)
- Branch: branch/i5
- Tests: 651 passed, 0 failed, 4 skipped, 3 warnings

## Wave 3 - I7: Tests for core/system_deps.py (CHUNK-I7)
- [Done] Created `tests/test_system_deps.py` with 17 tests for `check_gamemode()`
- [Done] Platform guard tests: macOS early return, Windows early return
- [Done] gamemoded found tests: returns None, emits info log
- [Done] gamemoded not found: emits warning log
- [Done] Package manager detection: apt, pacman, dnf, zypper individually verified
- [Done] No package manager fallback: manual install message verified
- [Done] Interactive install flow: success (subprocess.check_call), failure
  (CalledProcessError), generic exception (RuntimeError), user decline ('n')
- [Done] Non-interactive EOFError handling verified
- [Done] Output structure: MISSING DEPENDENCY banner, package manager priority order
  (apt wins over pacman when both present)
- Branch: branch/i7
- Tests: 737 passed, 0 failed, 4 skipped, 4 warnings
