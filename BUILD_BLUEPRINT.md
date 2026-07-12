# WowFactor v1.1.0 — Professional Build Blueprint

**Document Version:** 1.0  
**Date:** 2026-04-30  
**Author:** Architecture Lead  
**Scope:** Complete upgrade from hobbyist project to professional benchmark tool

---

## 1. VISION STATEMENT

WowFactor will become a **reproducible, accurate, extensible, well-tested, CI-backed, properly packaged** terminal-based CPU benchmarking tool that:

- Produces **reproducible** benchmark results with consistent methodology
- Delivers **accurate** measurements with proper warmup, frequency monitoring, and statistical rigor
- Is **extensible** through clean interfaces, typed APIs, and modular architecture
- Achieves **100% test coverage** across core logic with a proven CI/CD pipeline
- Is **professionally packaged** as a proper Python distribution with `pyproject.toml`

---

## 2. PROJECT STRUCTURE (Current)

```
WowFactor/
├── wowfactor.py                  # Entry point
├── requirements.txt              # Unpackaged dependencies
├── README.md                     # Exists but minimal
├── core/
│   ├── benchmark.py              # 702 lines — benchmark core, multiprocessing, data loading
│   ├── analytics_engine.py       # 552 lines — statistics, trend analysis, regression
│   ├── comparator.py             # 213 lines — cross-CPU comparison
│   ├── config.py                 # 232 lines — configuration management
│   ├── exporters.py              # 417 lines — CSV, JSON, XML, YAML exporters
│   ├── power.py                  # 192 lines — power plan management (Linux done, Windows stub)
│   └── system_deps.py            # System dependency checking
├── ui/
│   ├── app.py                    # Textual app, screen registry
│   ├── components.py             # 640 lines — DEPRECATED, duplicate screens + imports
│   ├── messages.py               # 64 lines — canonical message classes
│   ├── navigation.py             # 104 lines — singleton NavigationManager
│   ├── notifications.py          # 161 lines — ToastNotification system (BUGGY)
│   ├── layout_utils.py           # Shared layout helpers
│   ├── theme.py                  # Theme system
│   ├── shared.py                 # Shared header, gradient components
│   └── screens/
│       ├── benchmark.py          # 528 lines — BUG: duplicates messages, batch num_threads bug
│       ├── analytics.py          # Analytics UI screen
│       ├── views.py              # View best scores, compare CPUs, all scores screens
│       ├── main_menu.py          # Main menu screen
│       ├── profile_selection.py  # Profile selection
│       ├── cleanup.py            # Data cleanup screen
│       └── base_screen.py        # Base screen class
├── tests/                        # 22 test files, 60 passed / 9 failed / 1 skipped
├── benchmark_results/            # 633 JSON result files
├── data/archive/                 # Archive storage
├── docs/                         # Project documentation
├── logs/                         # Runtime logs
├── plans/                        # Existing blueprint files (legacy)
└── [ROOT CSV EXPORTS]            # Dead files + unwarranted CSV exports
```

---

## 3. CONFIRMED BUGS (Evidence-Based)

### BUG-1: Duplicate Message Classes
- **Location:** `ui/screens/benchmark.py:21-62` AND `ui/messages.py:10-64`
- **Classes duplicated:** `BenchmarkProgress`, `BenchmarkCompletion`, `BatchBenchmarkProgress`, `BatchBenchmarkCompletion`, `CooldownMessage`
- **Impact:** `ui/screens/benchmark.py` imports `execute_single_benchmark_run` from `ui/components.py`, but also redefines message classes. The `BatchBenchmarkCompletion` in benchmark.py takes `num_batch_runs` param while messages.py uses `total_batch_runs` — **INCOMPATIBLE SIGNATURES**.
- **Fix:** Remove all duplicated message class definitions from `ui/screens/benchmark.py`. Use only `ui/messages.py` as canonical source. Ensure `BatchBenchmarkCompletion` parameter name is consistent.

### BUG-2: ToastNotification Color Lookup
- **Location:** `ui/notifications.py:120-121`
- **Code:** `notification_type.value.bg_color`
- **Issue:** `NotificationType.value` is a plain string (`"success"`, `"error"`, etc.). String has no `.bg_color` attribute. The `hasattr` fallback catches this but silently falls back to blue.
- **Fix:** Use `ToastNotification.COLORS[notification_type]["bg"]` instead.

### BUG-3: CsvExporter.export() Writes Only Headers
- **Location:** `core/exporters.py:135-149`
- **Issue:** Method creates csv writer, writes header row, then **exits without writing a single data row**. Contrast with `AnalyticsExporter.export_stats_per_cpu()` (lines 198-214) which writes data rows correctly.
- **Fix:** Add data row writing loop following the pattern used by other exporters.

### BUG-4: RunBatchBenchmarkScreen Missing num_threads
- **Location:** `ui/screens/benchmark.py:395-397`
- **Code:**
  ```python
  def execute_single_benchmark_run(self, duration: float, is_infinite: bool, progress_callback):  # <-- NO num_threads
      # Pass default num_threads=1 for batch runs
      return execute_single_benchmark_run(duration, is_infinite, progress_callback=progress_callback)  # <-- num_threads NOT forwarded
  ```
- **Impact:** Batch benchmarks always run with 1 thread regardless of user settings.
- **Fix:** Add `num_threads` parameter to wrapper method, add thread count input to batch screen UI, pass through to core function.

### BUG-5: Multiprocessing Queue Serialization (4 test failures)
- **Error:** `RuntimeError: Queue objects should only be shared between processes through inheritance`
- **Root cause:** Tests instantiate `BenchmarkWorker` by passing Queue objects as constructor arguments, but the spawn start method requires queues to be set as instance attributes **before** process starts. The `_cpu_workload` function (legacy, unused in production) takes a queue as argument.
- **Fix:** Update test files to use `BenchmarkWorker` instantiation correctly with queues as instance attributes. Or mock the worker for unit tests.

### BUG-6: NavigationManager Not Initialized (5 test failures)
- **Error:** `RuntimeError: NavigationManager not initialized`
- **Root cause:** `conftest.py` does NOT initialize the NavigationManager singleton. Tests that import screens (which use `NavigationManager().navigate_to()`) fail because `_app` is None.
- **Fix:** Add pytest fixture in `conftest.py` that initializes NavigationManager with a mock or real app instance. Add `session`-scoped teardown that resets `_instance` and `_app`.

---

## 4. ATOMIC CHUNK CHECKLIST

Each chunk is independently assignable. Chunks marked `(Bug Fix)` are regression-prevented by existing tests once fixed. Chunks marked `(New Tests Required)` need dedicated test coverage.

### CATEGORY A: Critical Bug Fixes (Highest Priority)

#### A1: Fix CsvExporter.export() — Write Data Rows
- **File:** `core/exporters.py`
- **Change:** Add data row writing loop after header row in `CsvExporter.export()`. Each row should write: `id`, `cpu` (from `processor_model` or `system.processor_model`), `score` (from `ops_per_second`), `timestamp`, `platform`, `frequency` (from `processor_frequency` or `system.processor_frequency`), `threads` (from `num_threads`), `duration_seconds`, `total_operations`. Follow the exact same field extraction pattern as `XmlExporter.export()` for consistency.
- **Verification:** Write unit test that calls `CsvExporter.export()` with sample scores, reads the file, and asserts 1 header row + N data rows with correct values.
- **Dependencies:** None

#### A2: Fix ToastNotification Color Lookup Bug
- **File:** `ui/notifications.py`
- **Change:** Replace lines 120-121:
  ```python
  # FROM:
  toast_label.styles.background = notification_type.value.bg_color if hasattr(...) else "#17a2b8"
  toast_label.styles.color = notification_type.value.fg_color if hasattr(...) else "#ffffff"
  # TO:
  toast_label.styles.background = ToastNotification.COLORS[notification_type]["bg"]
  toast_label.styles.color = ToastNotification.COLORS[notification_type]["fg"]
  ```
- **Verification:** Test that `ToastNotification.show()` creates labels with correct colors for all 4 notification types (SUCCESS, ERROR, WARNING, INFO).
- **Dependencies:** None

#### A3: Deduplicate Message Classes
- **File:** `ui/screens/benchmark.py`
- **Change:**
  1. Remove class definitions for `BenchmarkProgress`, `BenchmarkCompletion`, `BatchBenchmarkProgress`, `BatchBenchmarkCompletion`, and `CooldownMessage` (lines 21-62).
  2. Add import: `from ui.messages import BenchmarkProgress, BenchmarkCompletion, BatchBenchmarkProgress, BatchBenchmarkCompletion, CooldownMessage`
  3. Update any references to `num_batch_runs` -> `total_batch Runs` to match `ui/messages.py` canonical parameter names.
- **Verification:** Run full test suite; verify no import errors; verify screens still post and receive messages correctly.
- **Dependencies:** None

#### A4: Fix Missing num_threads in Batch Benchmark
- **File:** `ui/screens/benchmark.py`
- **Changes:**
  1. Update `RunBatchBenchmarkScreen.execute_single_benchmark_run()` (line 395) to accept `num_threads` parameter and pass it through.
  2. Update `RunBatchBenchmarkScreen._batch_benchmark_worker_function()` to accept `num_threads` parameter.
  3. Add `Input` widget for thread count in `RunBatchBenchmarkScreen.compose()`.
  4. Update `start_batch_benchmark()` to read thread count and pass it to worker function.
  5. Update `run_worker` call to include `num_threads`.
- **Verification:** Integration test for batch benchmark flow with multiple threads.
- **Dependencies:** A3 (message dedup)

#### A5: Fix NavigationManager Initialization in Tests
- **File:** `tests/conftest.py`
- **Change:**
  1. Import `NavigationManager` from `ui.navigation`.
  2. Add `pytest.fixture(scope="session", autouse=True)` that creates a minimal mock app, calls `NavigationManager().initialize(mock_app)`, and yields.
  3. Add session-scoped `teardown` that sets `NavigationManager._instance = None` and `NavigationManager._app = None`.
  4. Optionally: add per-test fixture that resets NavigationManager state for isolation.
- **Verification:** Rerun tests; verify 5 previously-failing tests now pass.
- **Dependencies:** None

#### A6: Fix Multiprocessing Queue Serialization in Tests
- **Files:** Affected test files (identify via test failure output)
- **Change Options:**
  - **Option A (Preferred):** Mock `BenchmarkWorker.run()` or `multiprocessing.Queue` in unit tests. Use `unittest.mock.patch` to prevent actual process spawning in tests.
  - **Option B:** Use fork-style start method in test environment only by setting environment variable and catching `AssertionError` from `set_start_method`.
  - **Option C:** Create test-specific worker class that doesn't spawn processes but simulates the same logic.
- **Recommended:** Option A — use `pytest-mock` or `unittest.mock` to patch `BenchmarkWorker` and `multiprocessing` calls in test files.
- **Verification:** Rerun tests; verify 4 previously-failing tests now pass.
- **Dependencies:** A5 (NavigationManager fix needed for test infrastructure)

---

### CATEGORY B: Project Hygiene

#### B1: Create pyproject.toml
- **File:** `pyproject.toml` (NEW)
- **Contents:**
  - `[build-system]` with `setuptools` backend
  - `[project]` with name, version (1.1.0), description, authors, license, classifiers
  - Dependencies: `textual`, `psutil`, `py-cpuinfo`, `textual-plotext`, `plotext`
  - `[project.optional-dependencies]` with `dev` group: `pytest`, `pytest-asyncio`, `pytest-cov`, `ruff`, `pre-commit`
  - `[project.scripts]` with `wowfactor = "wowfactor:main"`
  - `[tool.ruff]` configuration
  - `[tool.pytest.ini_options]` configuration
  - `[tool.mypy]` configuration (optional, if adding type checking)
- **Verification:** `pip install -e ".[dev]"` succeeds; `pip list` shows wowfactor; `wowfactor` CLI entry point works.
- **Dependencies:** None

#### B2: Create Professional README.md
- **File:** `README.md` (REWRITE)
- **Sections:**
  - Project banner/hero line
  - Feature list (benchmark execution, analytics, comparison, export, power management)
  - Installation (from source, from PyPI if published)
  - Quick start (run benchmark, view results)
  - Screenshot/terminal output example (ASCII art rendering of TUI)
  - Configuration (config file location, supported options)
  - Architecture overview (diagram or description)
  - Development (running tests, contributing guidelines)
  - License
- **Verification:** Readable, complete, professional appearance.
- **Dependencies:** B1 (pyproject.toml for install instructions)

#### B3: Clean Up Dead Files
- **Files to REMOVE:**
  - `fix_test.py` (dead test fix script)
  - `fix_assertions.py` (dead assertion fix script)
  - `fix_test_assertions.py` (dead assertion fix script)
  - `pytest_full_output.txt` (dead test output log)
- **Files to MOVE to `data/exports/`:**
  - `all_scores_*.csv` (24 files)
  - `best_scores_*.csv` (15 files)
  - `cpu_comparison_*.csv` (15 files)
  - `all_scores.csv`, `best_scores.csv` (all non-timestamped versions)
- **Verification:** No dead files in root; CSV files not in root directory.
- **Dependencies:** None

#### B4: Organize CSV Exports into data/ Directory
- **File:** `core/exporters.py` (minor update)
- **Change:** Add `EXPORTS_DIR = "data/exports"` constant. Update any exporter or export-related code that writes to root directory to use `data/exports/` instead. Create directory if missing.
- **Verification:** Running exports creates files in `data/exports/`.
- **Dependencies:** B3 (move existing files)

#### B5: Improve .gitignore
- **File:** `.gitignore` (UPDATE)
- **Add patterns:**
  ```
  *.csv                          # Generated CSV exports
  .pytest_cache/                 # Pytest cache
  .coverage                      # Coverage data
  coverage.xml                   # Coverage report
  htmlcov/                       # HTML coverage
  .ruff_cache/                   # Ruff cache
  .mypy_cache/                   # Mypy cache
  .pre-commit-config.yaml.bak    # Backup configs
  *.pyc, __pycache__/            # Already there but verify
  data/exports/                  # Generated exports
  *.log                          # Log files
  ```
- **Verification:** `git status` shows no tracked generated files.
- **Dependencies:** B3, B4

---

### CATEGORY C: Code Quality

#### C1: Add Type Hints to core/benchmark.py
- **File:** `core/benchmark.py`
- **Change:**
  - Add type hints to all functions and methods: `clean_cpu_model_name`, `get_cpu_info`, `format_large_number`, `_get_all_valid_scores`, `save_benchmark_results`, `_cpu_workload`, `execute_single_benchmark_run`, `get_best_score_per_machine`, `get_scores_for_cpu`, `get_unique_cpu_models`, `cleanup_invalid_scores`, `parse_date`, `is_date_in_range`, `get_unique_platforms`, `apply_all_filters`, `aggregate_scores_by_cpu`, `get_score_distribution`, `export_data_to_json`, `setup_logging`.
  - Type-annotate `BenchmarkWorker` class: constructor, `run` method.
  - Type-annotate `DependencyCache` class methods.
  - Function-level `def _monitor_cpu_freq(...)` type hints.
- **Verification:** `ruff check --select=ANN` passes (or equivalent type lint).
- **Dependencies:** None

#### C2: Add Type Hints to core/analytics_engine.py
- **File:** `core/analytics_engine.py`
- **Change:** Add type hints to all public and private methods in `AnalyticsEngine` class and any module-level functions.
- **Return types:** Use `List`, `Dict`, `Tuple`, `Optional`, `Any` from `typing`. For complex outputs, create TypedDict or dataclass definitions.
- **Verification:** `ruff check --select=ANN` passes.
- **Dependencies:** None

#### C3: Add Type Hints to core/comparator.py
- **File:** `core/comparator.py`
- **Change:** Add full type annotations to `CPUComparator` class and methods.
- **Verification:** `ruff check --select=ANN` passes.
- **Dependencies:** None

#### C4: Add Type Hints to core/config.py
- **File:** `core/config.py`
- **Change:** Add type hints to config class/methods. Consider converting to dataclass with type defaults.
- **Verification:** `ruff check --select=ANN` passes.
- **Dependencies:** None

#### C5: Add Type Hints to core/exporters.py
- **File:** `core/exporters.py`
- **Change:** Add type hints to `XmlExporter`, `YamlExporter`, `CsvExporter`, `AnalyticsExporter` static methods. Most methods already have `List[Dict[str, Any]]` hints — verify completeness.
- **Verification:** `ruff check --select=ANN` passes.
- **Dependencies:** None

#### C6: Add Type Hints to core/power.py
- **File:** `core/power.py`
- **Change:** Add type hints to `PowerPlanManager` context manager methods.
- **Verification:** `ruff check --select=ANN` passes.
- **Dependencies:** None

#### C7: Remove Deprecated ui/components.py Duplicates
- **File:** `ui/components.py` (DELETE or DEPRECATE)
- **Analysis:**
  - File is 640 lines. Imports from `ui.messages.py` (canonical messages), then re-exports and defines duplicate screen components.
  - `ui/screens/benchmark.py` imports `execute_single_benchmark_run` and `LoadingOverlay` from `ui.components`.
- **Change:**
  1. Extract `LoadingOverlay` widget class to `ui/shared.py` (where it belongs with other shared components).
  2. Ensure `execute_single_benchmark_run` is imported from `core.benchmark` directly (not via `ui.components`).
  3. Update all import statements across codebase that reference `ui.components`.
  4. Add `__getattr__` deprecation shim to `ui/components.py` with 1-month deprecation warning, OR delete file entirely if no external dependencies.
  5. Check `ui/screens/` and `tests/` for remaining `ui.components` imports and redirect them.
- **Verification:** Run full test suite after removal; ensure all imports resolve.
- **Dependencies:** A3, A4 (bug changes affect components dependencies)

#### C8: Standardize Error Handling — WowFactorError Hierarchy
- **File:** `core/exceptions.py` (NEW), then update consumers
- **Hierarchy:**
  ```
  WowFactorError (base, inherits Exception)
  ├── BenchmarkError
  │   ├── BenchmarkCancelledError
  │   └── BenchmarkTimeoutError
  ├── AnalyticsError
  │   └── DataInsufficientError
  ├── ExportError
  │   └── FormatUnsupportedError
  ├── ConfigError
  │   └── ConfigValidationError
  └── SystemError
      └── PermissionError (specialize for governor operations)
  ```
- **Change:** Create exception classes. Update `core/benchmark.py`, `core/analytics_engine.py`, `core/exporters.py`, and `core/power.py` to raise these instead of generic `Exception`.
- **Verification:** Test that exceptions propagate correctly; verify `raise_from` chains.
- **Dependencies:** None

---

### CATEGORY D: Testing

#### D1: Fix All 9 Failing Tests
- **Files:** Identified via test run output
- **Changes:** This is the direct result of fixing bugs A1 through A6 and updating the affected test files. Specific fixes per test:
  - Tests failing on `RuntimeError: NavigationManager not initialized`: Fixed by A5.
  - Tests failing on `RuntimeError: Queue objects...`: Fixed by A6.
  - Tests failing on CsvExporter: Fixed by A1.
  - Tests failing on message class mismatch: Fixed by A3.
  - Tests failing on batch benchmark: Fixed by A4.
- **Verification:** `.venv/bin/python3 -m pytest tests/ -v` returns 0 failures.
- **Dependencies:** A1 through A6

#### D2: Add Test Coverage for analytics_engine (if gaps exist)
- **File:** `tests/test_analytics_engine.py` (UPDATE)
- **Target coverage:** 
  - `generate_summary_report()` with various data sets (empty, single entry, multiple entries)
  - Trend detection (upward, downward, flat, volatile)
  - Statistical calculations (mean, median, mode, stddev) with edge cases
  - Pairwise comparison logic
  - Outlier detection
- **Verification:** `pytest --cov=core/analytics_engine --cov-report=term-missing` shows >90% coverage.
- **Dependencies:** A3 (message dedup may affect analytics message usage)

#### D3: Add Test Coverage for Exporters
- **File:** `tests/test_exporters.py` (UPDATE)
- **Target coverage:** Every exporter method tested with data, empty data, malformed data.
- **New tests (enabled by A1):**
  - `CsvExporter.export()` writes correct number of rows with correct field values
  - `CsvExporter.export()` handles empty scores list gracefully
  - `XmlExporter.export()` validates XML structure (parse with `xml.etree.ElementTree`)
  - `YamlExporter.export()` validates YAML structure
  - `AnalyticsExporter` all methods
- **Verification:** `pytest --cov=core/exporters --cov-report=term-missing` shows >95% coverage.
- **Dependencies:** A1 (CsvExporter fix required for meaningful tests)

#### D4: Add Test Coverage for notifications and layout_utils
- **File:** `tests/test_notifications.py` (NEW), `tests/test_layout_utils.py` (NEW or UPDATE)
- **Tests:**
  - `ToastNotification` properties: `bg_color`, `fg_color`, `elapsed_time`, `is_expired` for each NotificationType
  - `ToastNotification.show()` creates correct colors (enabled by A2 fix)
  - `layout_utils` functions: each function with valid/invalid inputs
- **Verification:** `pytest --cov=ui/notifications --cov=ui/layout_utils --cov-report=term-missing` shows >90% coverage.
- **Dependencies:** A2 (notification fix)

#### D5: Add Test Coverage for NavigationManager
- **File:** `tests/test_navigation.py` (NEW)
- **Tests:**
  - `navigate_to()` with valid screen name pushes correct screen
  - `navigate_to()` with invalid screen name raises `ValueError`
  - `go_back()` pops screen correctly
  - `reset_to_main()` pops all screens to main menu
  - `notify()` displays correct notification type
  - Uninitialized state raises `RuntimeError`
  - Singleton behavior verified
- **Verification:** All tests pass; `pytest --cov=ui/navigation --cov-report=term-missing` shows >90%.
- **Dependencies:** A5 (NavigationManager test infrastructure)

#### D6: Create Test for CsvExporter Data Writing
- **File:** `tests/test_exporters.py` (ADD to existing)
- **Tests to add:**
  - `test_csv_export_writes_data_rows()`: 3 score entries -> file has 4 lines (header + 3 data)
  - `test_csv_export_field_accuracy()`: verify each column maps to correct field
  - `test_csv_export_empty_scores()`: empty list -> file has only header row
  - `test_csv_export_nested_system_fields()`: scores with `system` dict structure handled correctly
- **Verification:** Tests pass against fixed `CsvExporter`.
- **Dependencies:** A1 (CsvExporter fix)

---

### CATEGORY E: Professional Infrastructure

#### E1: Create GitHub Actions CI/CD Workflow
- **File:** `.github/workflows/ci.yml` (NEW)
- **Pipeline stages:**
  1. **Lint**: `ruff check .` on Python 3.13, Ubuntu latest
  2. **Test**: `pytest tests/ -v --tb=short` on Python 3.12 and 3.13
  3. **Coverage**: Upload `coverage.xml` to codecov.io (optional)
  4. **Type Check**: Optional mypy check (if adding type hints)
- **Trigger:** `push` to `main`, `pull_request`
- **Matrix:** Python 3.12, 3.13 (core benchmark logic shouldn't be version-dependent)
- **Verification:** Push to feature branch; verify Action runs and passes.
- **Dependencies:** B1 (pyproject.toml), B5 (.gitignore), E4 (lint config)

#### E2: Add pytest Configuration
- **File:** `pyproject.toml` (UPDATE — add under `[tool.pytest.ini_options]`)
- **Configuration:**
  ```toml
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  python_files = ["test_*.py"]
  python_classes = ["Test*"]
  python_functions = ["test_*"]
  addopts = [
      "-v",
      "--tb=short",
      "--strict-markers",
  ]
  # Markers used in tests
  markers = [
      "slow: marks tests as slow",
      "integration: marks integration tests",
  ]
  ```
- **Verification:** `pytest` runs without needing CLI arguments.
- **Dependencies:** B1 (pyproject.toml)

#### E3: Add Pre-Commit Hooks Configuration
- **File:** `.pre-commit-config.yaml` (NEW)
- **Hooks:**
  - `ruff`: lint and format
  - `ruff-format`: code formatting
  - `trailing-whitespace`: strip trailing whitespace
  - `end-of-file-fixer`: ensure trailing newline
  - `check-yaml`: validate YAML files
  - `check-toml`: validate TOML files
  - `check-added-large-files`: prevent large file commits
- **Verification:** `pre-commit run --all-files` passes.
- **Dependencies:** B1 (pyproject.toml for dev deps), E4 (ruff config)

#### E4: Add Python Linting (Ruff Configuration)
- **File:** `pyproject.toml` (UPDATE — add under `[tool.ruff]`)
- **Configuration:**
  ```toml
  [tool.ruff]
  target-version = "py312"
  line-length = 120
  src = ["core", "ui", "tests"]
  
  [tool.ruff.lint]
  select = [
      "E",      # pycodestyle errors
      "W",      # pycodestyle warnings
      "F",      # pyflakes
      "I",      # isort (import sorting)
      "N",      # pep8-naming
      "UP",     # pyupgrade
      "B",      # flake8-bugbear
  ]
  ignore = [
      "E501",   # line length (enforced by formatter)
  ]
  
  [tool.ruff.lint.per-file-ignores]
  "__init__.py" = ["F401"]  # unused imports in __init__.py are OK
  "tests/*.py" = ["E402"]   # module level import not at top of file (common in tests)
  
  [tool.ruff.format]
  quote-style = "double"
  indent-style = "space"
  ```
- **Verification:** `ruff check .` passes (after fixing all lint violations).
- **Dependencies:** B1 (pyproject.toml)

---

### CATEGORY F: Feature Enhancements

#### F1: Implement Windows Power Management
- **File:** `core/power.py`
- **Changes:**
  - Implement `_enter_windows()`: Run `powercfg /S 8c5e7f7e-6870-4ee3-9a0c-3b4b9d07af36` (Ultimate Performance GUID) or `powercfg /S SCHEME_HIGH_PERF` (High Performance fallback).
  - Implement `_exit_windows()`: Run `powercfg /S SCHEME_BALANCED` (balanced power plan GUID `381b4222-f694-41f0-9685-ff5bb260df2e`).
  - Capture `powercfg /LIST` to identify available schemes programmatically (avoid hardcoded GUIDs).
  - Handle elevation requirements (may need admin rights — log warning if `Access is denied`).
  - Handle `powercfg` not found (Windows without power management tools — shouldn't happen, but defensive).
- **Verification:** Code review (cannot test on Linux). Mock `subprocess.run` in tests to verify correct commands are constructed.
- **Dependencies:** None

#### F2: Make WARMUP_DURATION and CACHE_TTL Configurable
- **File:** `core/benchmark.py`, `core/config.py` (UPDATE)
- **Changes:**
  1. Add to config schema: `warmup_duration` (float, default 5.0) and `cache_ttl` (int, default 300).
  2. Replace hardcoded `WARMUP_DURATION = 5.0` and `_CACHE_TTL = 300` with reads from config.
  3. Update `BenchmarkWorker.__init__` to accept warmup_time from config (already accepts `warmup_time` parameter, just need to pass it from config).
  4. Update `DependencyCache` instantiation to use config TTL.
  5. Add environment variable override support: `WOWFACTOR_WARMUP_DURATION`, `WOWFACTOR_CACHE_TTL`.
- **Verification:** Tests run with custom warmup duration; verify benchmark completes in expected time.
- **Dependencies:** C4 (config type hints)

#### F3: Add Schema Validation for Benchmark Result JSON Files
- **File:** `core/validators.py` (NEW)
- **Implementation:**
  - Define JSON schema using `jsonschema` library or manual validation function.
  - Required fields: `timestamp` (ISO 8601 or "%Y-%m-%d %H:%M:%S"), `ops_per_second` (number > 0), `duration_seconds` (number > 0), `total_operations` (integer >= 0), `num_threads` (integer >= 1), `system.platform` (string), `system.processor_model` (string), `system.processor_frequency` (string).
  - Function `validate_benchmark_result(data: Dict) -> bool` that returns True/False.
  - Hook into `_get_all_valid_scores()` to reject invalid files silently (currently handles JSONDecodeError but not schema-level validation).
- **Verification:** Test with malformed data (missing fields, wrong types, negative values); verify invalid files are rejected.
- **Dependencies:** None

#### F4: Improvements Already Covered by A1
- **Note:** `CsvExporter` fix (A1) already addresses the data writing gap. This chunk references A1 for completeness tracking.
- **No additional work needed.**

#### F5: Add Headless CLI Mode (Non-Interactive Benchmarking)
- **File:** `wowfactor.py` (UPDATE) or `__main__.py` (NEW)
- **Implementation:**
  1. Add `argparse` CLI interface supporting:
     - `wowfactor run [duration] [--threads N]` — run benchmark headlessly
     - `wowfactor analyze` — load results, print summary report to stdout
     - `wowfactor compare [cpu1] [cpu2]` — print comparison to stdout
     - `wowfactor export --format csv|json|xml|yaml --output FILE` — export results to file
     - `wowfactor --version` — print version
  2. Implement `run_benchmark_headless(duration, threads)` in `core/benchmark.py` that calls `execute_single_benchmark_run` with a no-op progress callback and prints results to stdout.
  3. Implement `print_analytics()` that calls `AnalyticsEngine` and prints formatted text summary.
  4. Keep TUI as default when no arguments given (backward compatible).
- **Verification:** Run `python wowfactor.py run 5 --threads 2` and verify benchmark executes and prints results. Run `wowfactor analyze` and verify summary output.
- **Dependencies:** A1 through A6 (bug fixes ensure reliable headless execution), C8 (error hierarchy for clean error messages)

---

## 5. IMPLEMENTATION ORDER (Critical Path)

```
Phase 1 — Stabilization (Week 1)
├── A5 (NavigationManager test fix)        ← Unblocks test infrastructure
├── A6 (Multiprocessing Queue fix)          ← Unblocks remaining test failures  
├── A1 (CsvExporter fix)                    ← Bug fix, enables D6
├── A2 (ToastNotification fix)              ← Bug fix, enables D4
├── A3 (Message dedup)                      ← Bug fix, cleanup
└── A4 (Batch num_threads fix)              ← Bug fix, depends on A3

Phase 2 — Test Parity (Week 1-2)
├── D1 (Fix all 9 failing tests)            ← Depends on all A* fixes
├── D6 (CsvExporter data writing test)      ← Depends on A1
├── D4 (Notifications + layout_utils tests) ← Depends on A2
└── D5 (NavigationManager tests)            ← Depends on A5

Phase 3 — Project Hygiene (Week 2)
├── B1 (pyproject.toml)                     ← Unblocks CI
├── B5 (.gitignore)                         ← Dependencies: B3, B4
├── B3 (Dead file cleanup)
├── B4 (CSV organization)
└── B2 (Professional README)               ← Dependency: B1

Phase 4 — Code Quality (Week 2-3)
├── C1-C6 (Type hints across core/)         ← Parallel chunks, independent
├── C8 (Error hierarchy)                    ← Independent
└── C7 (Remove components.py duplicates)    ← Dependency: A3, A4

Phase 5 — Testing Expansion (Week 3)
├── E2 (pytest config)                      ← Dependency: B1
├── D2 (analytics coverage)
└── D3 (exporter coverage)                  ← Dependency: A1

Phase 6 — Professional Infrastructure (Week 3-4)
├── E4 (Ruff lint config)                   ← Dependency: B1
├── E3 (Pre-commit hooks)                   ← Dependency: E4
└── E1 (GitHub Actions CI)                  ← Dependency: B1, B5, E4

Phase 7 — Feature Enhancements (Week 4+)
├── F2 (Configurable warmup/cache)          ← Dependency: C4
├── F5 (Headless CLI mode)                  ← Dependency: A1-A6, C8
├── F1 (Windows power management)           ← Independent
└── F3 (JSON schema validation)             ← Independent
```

---

## 6. DEFINITION OF DONE

The upgrade is considered **COMPLETE** when:

1. [ ] All 9 failing tests pass (target: 0 failures, 0 errors)
2. [ ] New test coverage brings total to >70% on core modules (`--cov=core`)
3. [ ] `ruff check .` and `ruff format --check .` pass with zero violations
4. [ ] `pyproject.toml` correctly defines build system, dependencies, and scripts
5. [ ] `pip install -e ".[dev]"` installs all dependencies
6. [ ] GitHub Actions CI pipel ine passes green on main branch
7. [ ] No dead files in project root
8. [ ] `ui/components.py` removed or deprecated
9. [ ] All core modules (`benchmark.py`, `analytics_engine.py`, `comparator.py`, `config.py`, `exporters.py`, `power.py`) have type hints
10. [ ] `CSVExporter.export()` writes data rows correctly

---

## 7. RISK ASSESSMENT

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Multiprocessing spawn on macOS breaks tests | Medium | High | Ensure CI tests exclude multiprocessing unit tests on macOS or mock appropriately |
| Textual version incompatibility with Python 3.13 | Low | High | Pin textual version in pyproject.toml; test on both 3.12 and 3.13 in CI matrix |
| Removing `ui/components.py` breaks untracked imports | Medium | Medium | Grep entire codebase for `from ui.components import` before removal; fix all |
| Message class dedup changes event handling | Low | High | Thoroughly verify `BatchBenchmarkCompletion` parameter names match all post_message() calls |
| Headless CLI interferes with TUI startup | Low | Medium | Use `sys.argv` detection; fallback to TUI when no args match CLI commands |

---

## 8. ROLLING STATE BLOCK

```
@@@ CURRENT_STATE @@@
Phase: BLUEPRINT_COMPLETE
Status: BUILD_BLUEPRINT.md created at /mnt/Optane/Documents/WowFactor/BUILD_BLUEPRINT.md
Next: Begin Phase 1 — Stabilization (A1 through A6 bug fixes)
Total chunks: 35 (A1-A6, B1-B5, C1-C8, D1-D6, E1-E4, F1-F5)
Critical path: A5 -> A6 -> A1-A4 -> D1 -> B1 -> E2-E4 -> E1
```
