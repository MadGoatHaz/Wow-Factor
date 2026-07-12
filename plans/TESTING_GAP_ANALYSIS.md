# Testing Gap Analysis — WowFactor TUI

**Date:** 2026-07-12
**Scope:** 28 test files, 313 passing tests
**File count analyzed:** All `tests/**/*.py`, all `ui/**/*.py`, `core/*.py` (surface-level)
**Tooling:** pytest + unittest (mixed), heavy use of `MagicMock`/`patch`, no Textual `App.run_test()` usage

---

## Executive Summary

The test suite has 313 passing tests, but **all 3 runtime crashes** (TCSS docstring, worker API misuse, missing `current_screen` attribute) slipped through because the tests are **unit-level mocks only**. Every test either:
- Instantiates a class and checks attributes (pass/fail by inspection), or
- Patches all I/O and component interactions, then calls a single method, or
- Reads files as plain text (no Textual runtime), or

**No test ever runs inside a Textual `App` event loop context.** This means the `App` lifecycle (`__init__` -> `on_mount` -> `push_screen` -> compose), the Textual CSS parser, and Textual's `run_worker()` API contract are never exercised at runtime.

---

## 1. What the Current Test Suite Tests (Categories)

| # | Category | Test File(s) | Test Count | What It Verifies |
|---|----------|-------------|------------|-------------------|
| 1 | **App structure** | `test_app_comprehensive.py` | ~30 | Instantiation, SCREENS dict, CSS_PATH string, layout_manager attr |
| 2 | **Screen instantiation** | `test_app_comprehensive.py` | ~15 | Every screen class can be `__init__()`-ed without error |
| 3 | **NavigationManager unit** | `test_navigation.py` | ~20 | Singleton, initialize, navigate_to/go_back/reset_to_main/notify with mocked app |
| 4 | **ToastNotification** | `test_notifications.py` | ~25 | Init, colors, expiration, dismiss, stacking, schedule_auto_dismiss |
| 5 | **Worker callable check (mocked)** | `test_app_comprehensive.py` | 2 | `run_worker` is called with a lambda — but mock replaces actual Textual impl |
| 6 | **Threading/Screen UI integration** | `test_threading_ui_integration.py` | 4 | Validates duration/threads input, mocks `run_worker`, checks UI state, checks completion notification |
| 7 | **ConfigManager** | `test_config_manager.py` | ~15 | Defaults, profiles CRUD, `to_dict`/`from_dict` |
| 8 | **Aggregation** | `test_aggregation.py` | 8 | `aggregate_scores_by_cpu`, `get_score_distribution` |
| 9 | **Comparator** | `test_comparator.py` | ~10 | Results comparison, best run, stats |
| 10 | **Exporters** | `test_exporters.py`, `test_export_formats.py` | ~45 | Xml/Yaml/Csv/Json export with valid, empty, special-char, unicode, large datasets |
| 11 | **Charts UI data flow** | `test_charts_ui.py` | 1 | AnalyticsScreen.render_charts data passes to mocked PlotextPlot |
| 12 | **Power management** | `test_power_management.py` | 4 | PowerPlanManager enter/exit with permission errors |
| 13 | **Benchmarker core** | `test_benchmark_worker.py` | ~15 | Many xfail (removed classes), a few passing format/queue tests |
| 14 | **Thread timing** | `test_threading_logic.py` | 3 | Real `execute_single_benchmark_run` with 1–4 threads |
| 15 | **CSS file validation** | `test_app_comprehensive.py` (TestCSSValidation) | 4 | File exists, not empty, no `"""` prefix, `Stylesheet.read()` parses |
| 16 | **Message classes** | `test_app_comprehensive.py` (TestMessages) | 9 | All custom message classes instantiate correctly |
| 17 | **Loading state** | `test_loading_states.py` | ~10 | Presence of `load_data`, `_update_table_*`, `_show_error_message` methods |
| 18 | **Export improvements** | `test_export_improvements.py` | 3 | `export_to_csv()` on 3 view screens with mocked tables |
| 19 | **CPU/sleep** | `test_cpu_sleep.py` | 1-2 | Duration check, xfail for infinite |
| 20 | **Error handling (standalone)** | `test_error_handling.py` | 1 | Print-based runner script, not pytest-compatible |
| 21 | **Final functionality** | `test_final_functionality.py` | 6 | Print-based runner, imports + structure checks |
| 22 | **Worker cancel (no-op)** | `test_worker_cancel_proper.py` | 0 | Empty file |

**Coverage spectrum:** The suite heavily covers **pure Python logic** (exporters, aggregation, comparator, config). It has **light UI coverage** limited to method-presence checks and mocked callback invocations. It has **zero app-lifecycle coverage**.

---

## 2. What the Test Suite DOES NOT Test (Gap Inventory)

### 2.1 App Lifecycle / Textual Runtime

| Gap | Description | Why It Mattered |
|-----|-------------|-----------------|
| **A1** | App never starts via `App.run_test()` or `async with App()` | The CSS parser, widget composition, and screen lifecycle are never exercised. |
| **A2** | No test verifies `on_mount()` executes `navigation.initialize(self)` and `push_screen("main_menu")` | If `on_mount` fails, the app starts without a main screen — no test catches this. |
| **A3** | No test verifies that after `push_screen("main_menu")`, `app.current_screen` is a `MainMenuScreen` instance | Bug #3 (missing `current_screen`) stems from navigating before the screen is fully active. |
| **A4** | No test runs the full app startup: `WowFactorTUI()` -> `on_mount()` -> compose -> render | The CSS parser sees `styles.tcss` in a different context than `Stylesheet.read()` alone. |

### 2.2 Textual CSS/Stylesheet Runtime

| Gap | Description | Why It Mattered |
|-----|-------------|-----------------|
| **B1** | `test_styles_tcss_parseable` calls `Stylesheet().read(path)` directly, bypassing Textual's `App` CSS loading path | Textual may handle CSS errors differently during `App.__init__` vs standalone `Stylesheet.read()`. |
| **B2** | No test verifies the CSS_PATH resolves relative to the app module directory (not CWD) | If tests run from `tests/` directory, relative path resolution differs from app startup. |
| **B3** | No test verifies CSS selectors used in screens (`#duration_input`, `#start_benchmark`, `#progress_display`, etc.) exist in styles.tcss | Screens reference many IDs that styles.tcss doesn't define — silent fallback to defaults, not a test failure. |
| **B4** | No test validates that compose() yields valid widget hierarchies inside a Textual app context | All 12 compose tests are marked `xfail`. |

### 2.3 Worker / Threading Runtime

| Gap | Description | Why It Mattered |
|-----|-------------|-----------------|
| **C1** | `run_worker()` is mocked in `test_threading_ui_integration.py` (line 15: `self.screen.run_worker = MagicMock()`) | The actual Textual `run_worker()` API contract — "accepts callable or coroutine" — is never tested with the real implementation. |
| **C2** | `test_app_comprehensive.py:5 test_single_benchmark_worker_callable` patches `run_worker` before calling it | The patched method never receives the first argument, so the callable check is meaningless. |
| **C3** | No test calls `start_benchmark_run()` on an unmocked screen with a real `run_worker` stub | The lambda/coroutine creation logic is not tested end-to-end. |
| **C4** | Batch worker (`start_batch_benchmark`) is never tested for its async `run_worker` call (no `thread=True`) | The async path has different Textual runtime semantics. |

### 2.4 Navigation Lifecycle

| Gap | Description | Why It Mattered |
|-----|-------------|-----------------|
| **D1** | `test_navigation.py` uses a hand-rolled `MockApp` that defines `current_screen = None` | Bug #3: real `WowFactorTUI` (Textual App) doesn't have `current_screen` set until after the app loop runs. |
| **D2** | `notify()` is tested only with mocked `ToastNotification.show()` — the UI mounting logic is never exercised | Toast creation (`ToastNotification.show()`) mounts widgets into the parent screen. If the screen isn't in the app tree, this fails at runtime. |
| **D3** | No test verifies `go_back()` followed by `notify()` works in sequence (the exact pattern in `on_benchmark_completion`) | After `go_back()`, the current screen changes. `notify()` must work with the new screen. |
| **D4** | No test covers the screen push/pop lifecycle: push loading_overlay -> run benchmark -> go_back -> notify | This is the exact flow from bug #3. |

### 2.5 User Interaction Flow

| Gap | Description | Why It Mattered |
|-----|-------------|-----------------|
| **E1** | No test simulates clicking the "Start" button (button press -> validation -> worker -> result) | Bug #2: the full click-to-completion flow is never exercised. |
| **E2** | No test simulates button presses on MainMenuScreen -> navigate_to -> screen composition | The full navigation chain is untested. |
| **E3** | No test covers user canceling a running benchmark (button -> cancel -> worker cancelled -> on_benchmark_completion) | Error path through worker cancellation is untested. |
| **E4** | No test covers the batch benchmark start/completion cycle | Batch flow is entirely untested. |

### 2.6 Screen-to-Screen State

| Gap | Description | Why It Mattered |
|-----|-------------|-----------------|
| **F1** | No test verifies that screens share navigation state correctly across pushes | NavigationManager is a singleton, but no test pushes/pops multiple screens and checks state. |
| **F2** | `reset_to_main()` is tested with hand-crafted screens, not real Textual screens | Behavior with Textual widget trees is unverified. |

### 2.7 Message Bus / Async Communication

| Gap | Description | Why It Mattered |
|-----|-------------|-----------------|
| **G1** | `post_message()` and `on_benchmark_progress/completion` handlers are never tested with real Textual message dispatch | Screens post messages, handlers receive them — but this async flow is mocked in `test_threading_ui_integration.py` (`post_message = MagicMock()`). |
| **G2** | No test verifies message type registration (Textual requires `watch_*` or `on_*` handlers to be registered) | If a handler name doesn't match Textual's convention, messages silently drop. |

---

## 3. Root Cause Analysis — Why the Test Suite Missed Each Bug

### Bug #1: TCSS parser error — Python docstring crashes Textual CSS parser

**Error:** A Python docstring (`"""..."""`) at the top of `styles.tcss` causes Textual's CSS parser to throw an error on app startup.

**What the test does:** `test_app_comprehensive.py:TestCSSValidation.test_styles_tcss_no_python_docstring` reads the file as text and asserts the first line doesn't start with `"""`.

**Why it missed:**
1. The test checks for a **string pattern** (`"""`), not for **parser behavior**. A docstring could be split across lines, use `'''`, or be in a comment-like position that passes the text check but fails the parser.
2. `test_styles_tcss_parseable` uses `Stylesheet().read(path)` directly — a **standalone** Textual API call. Textual's `App` class loads CSS differently: via `CSS_PATH` attribute in `App.__init__`, with different error handling and path resolution.
3. The test runs from the project root, but in practice the app might start from a different working directory, changing how `CSS_PATH` resolves.

**Test type that would have caught it:** An app-integration test that instantiates `WowFactorTUI()` inside `App.run_test()`. Textual would load `CSS_PATH`, parse `styles.tcss`, and raise if it encounters invalid CSS. The test would fail at `__init__` or `on_mount`.

### Bug #2: Worker API error — `run_worker()` called with executed result (None) instead of deferred callable

**Error:** User clicks "Start" → `start_benchmark_run()` → `self.run_worker(lambda: self._benchmark_worker_function(...), thread=True)` — if `_benchmark_worker_function` returns `None` and the lambda is callable but the Textual runtime detects something wrong, or if the lambda itself is poorly constructed, `run_worker` rejects it.

**What the test does:**
- `test_threading_ui_integration.py:45` mocks `run_worker`: `self.screen.run_worker = MagicMock()`. The real Textual `run_worker` is never called.
- `test_app_comprehensive.py:5 test_single_benchmark_worker_callable` patches `run_worker` and checks `assert callable(call_args[0][0])`. This passes because `lambda: None` is callable. Neither verifies the actual screen code path.

**Why it missed:**
1. **Mocks shield the real API.** All tests that call `start_benchmark_run()` (or simulate it) replace `run_worker` with a `MagicMock`. The mock accepts any arguments — including `None` — without complaint.
2. **No test exercises the actual Textual worker creation.** The Textual `run_worker()` method validates its first argument: it must be a callable or a coroutine function. If a screen passes the **result** of a call (e.g., `self.run_worker(some_function(), ...)` instead of `self.run_worker(some_function, ...)`), Textual raises `ValueError: First argument must be a callable or a coroutine`. This error is invisible to mock-based tests.
3. **The lambda in the code** wraps `_benchmark_worker_function` in a `lambda:` — if that inner method ever returns `None` before posting messages, the worker completes silently. No test verifies that the worker's lambda function is a proper deferred (it doesn't immediately execute).

**Test type that would have caught it:** An integration test using `screen.run_worker` that is **not mocked** — or at minimum, a test that passes the real lambda to a stub `run_worker` and asserts the first argument is callable AND that calling it doesn't immediately return `None` without posting a message.

### Bug #3: Navigation error — `AttributeError: 'WowFactorTUI' object has no attribute 'current_screen'`

**Error:** After benchmark completes, `on_benchmark_completion` calls `self.navigation.go_back()` (pops loading_overlay) then `self.navigation.notify(...)` which reads `self.app.current_screen`. Textual's App reports the error because `current_screen` is not yet initialized or accessible.

**What the test does:**
- `test_navigation.py` tests `notify()` with `app.current_screen = Mock()`. This **never fails** because the mock app explicitly defines `current_screen = None` (conftest) or sets it to a Mock.
- No test uses a real Textual `App` instance where `current_screen` might be a property that errors or returns None at specific lifecycle points.

**Why it missed:**
1. **MockApp defines `current_screen = None`** in both `conftest.py` (line 22) and `test_navigation.py` (line 25). These mocks **never exercise the actual Textual App property**, which may behave differently.
2. **No test pushes/pops screens** through a real Textual App. The flow in bug #3 is: push loading_overlay -> worker runs -> worker posts BenchmarkCompletion -> `on_benchmark_completion` calls `go_back()` -> `go_back()` pops the overlay -> `notify()` accesses `self.app.current_screen`. At this point, if the popped screen was the only screen in the stack and Textual hasn't updated `current_screen` yet, accessing it might error.
3. **Textual's `current_screen` is a property**, not a simple attribute. The property getter might raise if the app's internal state is inconsistent (e.g., between pop and re-render). The tests never create this state.

**Test type that would have caught it:** An integration test that creates an App, pushes a screen, pops it, and then calls a method that accesses `app.current_screen`. This would reproduce the timing gap.

---

## 4. Gap Taxonomy

```
┌─────────────────────────────────────────────────────────────┐
│                    GAP TAXONOMY                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. LIFECYCLE GAPS (3 gaps)                                 │
│     ┌─────────────────────────────────┐                     │
│     │ • No App.run_test() anywhere    │                     │
│     │ • on_mount() not exercised      │                     │
│     │ • Screen lifecycle not tracked  │                     │
│     └─────────────────────────────────┘                     │
│         All 3 runtime bugs stem from lifecycle timing.      │
│                                                             │
│  2. INTEGRATION GAPS (4 gaps)                               │
│     ┌─────────────────────────────────┐                     │
│     │ • Worker API not real           │                     │
│     │ • Screen-to-screen state flow   │                     │
│     │ • Message bus (post/on handlers)│                     │
│     │ • Button press → handler chain  │                     │
│     └─────────────────────────────────┘                     │
│         Tests mock everything that connects modules.          │
│                                                             │
│  3. RUNTIME GAPS (3 gaps)                                   │
│     ┌─────────────────────────────────┐                     │
│     │ • CSS parsed via standalone API │                     │
│     │ • current_screen property mock  │                     │
│     │ • ToastNotification.mount()     │                     │
│     └─────────────────────────────────┘                     │
│         Runtime-only behavior of Textual widgets/properties.  │
│                                                             │
│  4. USER INTERACTION GAPS (4 gaps)                          │
│     ┌─────────────────────────────────┐                     │
│     │ • Button click sequences        │                     │
│     │ • Start → work → complete flow  │                     │
│     │ • User cancel flow              │                     │
│     │ • Navigation menu traversal     │                     │
│     └─────────────────────────────────┘                     │
│         The UI's main user journeys are untested.             │
│                                                             │
│  5. CROSS-CUTTING GAPS                                      │
│     ┌─────────────────────────────────┐                     │
│     │ • 12 compose() methods xfailed  │                     │
│     │ • 50%+ tests are mock-only      │                     │
│     │ • No app-context isolation      │                     │
│     │ • test_worker_cancel_proper.py  │                     │
│     │   is empty (0 bytes)            │                     │
│     └─────────────────────────────────┘                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Recommendations — New Test Types

### 5.1 App Integration Tests (critical)

**File:** `tests/test_app_integration.py`

| Test | What It Verifies |
|------|-----------------|
| `test_app_startup_succeeds` | `async with App.run_test(WowFactorTUI())` completes without exception. Verifies CSS loading + on_mount + initial screen push. |
| `test_app_current_screen_after_mount` | After app mounts, `app.current_screen` is a `MainMenuScreen`. Verifies the screen is accessible on the App instance. |
| `test_screen_can_access_app_current_screen` | From within a mounted screen, `self.app.current_screen` is accessible. **Directly tests Bug #3 root cause.** |
| `test_app_css_loads_without_error` | Explicitly verify that `WowFactorTUI.CSS_PATH` loads without raising during `App.run_test()`. **Directly tests Bug #1 root cause.** |

### 5.2 Navigation Lifecycle Tests (critical)

**File:** `tests/test_navigation_lifecycle.py`

| Test | What It Verifies |
|------|-----------------|
| `test_push_pop_notify_sequence` | Push a screen, go_back, then call `navigation.notify()`. Verifies `current_screen` is valid after pop. **Directly tests Bug #3.** |
| `test_notify_with_textual_app` | Create a real Textual App, push a screen, call `notify()`. Verifies ToastNotification mounts correctly into the widget tree. |
| `test_screen_navigation_chain` | MainMenu -> RunBenchmark -> LoadingOverlay -> go_back -> MainMenu. Verifies full navigation flow with real App. |
| `test_notify_after_screen_removal` | Push screen, remove it, then call notify. Checks behavior when current_screen has changed. |

### 5.3 Worker Integration Tests (critical)

**File:** `tests/test_worker_integration.py` (replace existing stub)

| Test | What It Verifies |
|------|-----------------|
| `test_run_worker_receives_callable` | Call `start_benchmark_run()` on a screen inside `App.run_test()`. Capture what `run_worker` receives. Assert first arg is callable. **Directly tests Bug #2.** |
| `test_run_worker_async_batch` | Call `start_batch_benchmark()` similarly. Assert first arg is callable/coroutine. |
| `test_worker_lambda_not_immediately_executed` | Verify that passing a lambda to `run_worker` does not execute the lambda's body before the worker starts. |

### 5.4 Screen Interaction Tests

**File:** `tests/test_screen_interactions.py`

| Test | What It Verifies |
|------|-----------------|
| `test_main_menu_button_navigates` | Within `App.run_test()`, find the "Run New Benchmark" button, press it, verify screen changes. |
| `test_benchmark_start_button` | Find start button, press it, verify worker starts and UI state changes (buttons disabled). |
| `test_benchmark_completion_shows_results` | Mock the benchmark result, simulate completion, verify summary display updates and notification fires. |
| `test_validate_duration_input` | Set invalid duration, click start, verify error notification shown and worker NOT started. |
| `test_validate_thread_input` | Set invalid threads, click start, verify error notification and no worker. |

### 5.5 CSS & Compose Tests

**File:** `tests/test_compose_integration.py`

| Test | What It Verifies |
|------|-----------------|
| `test_main_menu_compose_successfully` | Run `App.run_test()` with a `MainMenuScreen`. Verify compose doesn't raise. |
| `test_benchmark_screen_compose_successfully` | Run `App.run_test()` with a `RunSingleBenchmarkScreen`. |
| `test_all_screens_compose` | Parameterized test: instantiate each screen class in a Textual app context and call compose(). |

### 5.6 End-to-End User Flow Tests

**File:** `tests/test_user_flows.py`

| Test | What It Verifies |
|------|-----------------|
| `test_benchmark_user_journey` | MainMenu -> Click Run -> Verify start button -> (mock worker result) -> Verify completion screen -> Click Back -> Verify back in main menu. |
| `test_cancel_benchmark` | Start benchmark -> click stop -> verify cancellation notification. |
| `test_view_scores_flow` | MainMenu -> Click View Best Scores -> Verify table loads -> Verify pagination exists. |
| `test_profile_selection_flow` | MainMenu -> Manage Profiles -> Verify profile list or empty state. |

### 5.7 CSS Selector Coverage

**File:** `tests/test_css_selector_coverage.py`

| Test | What It Verifies |
|------|-----------------|
| `test_all_widget_ids_referenced_in_css_or_have_defaults` | Extract all `id="..."` and `class="..."` references from screen compose methods. Verify each either exists in styles.tcss or Textual has a sensible default. |
| `test_no_duplicate_ids_across_screens` | Verify no two screens define the same widget ID. |

---

## 6. Prioritized Backlog of New Test Files

Priority ordering is based on **bug prevention impact** and **existing code maturity**.

### Priority 1: Must-create before next release

| # | File | Tests | Bugs Prevented | Effort |
|---|------|-------|----------------|--------|
| 1 | `test_app_integration.py` | 3-4 | Bug #1, Bug #3 | Low |
| 2 | `test_navigation_lifecycle.py` | 4 | Bug #3 | Low |
| 3 | `test_worker_integration.py` | 3 | Bug #2 | Medium |

### Priority 2: Should-create before next release

| # | File | Tests | Purpose | Effort |
|---|------|-------|---------|--------|
| 4 | `test_screen_interactions.py` | 5 | Button press → handler chains | Medium |
| 5 | `test_compose_integration.py` | 12 | Replace all 12 `xfail` compose tests | Low-Medium |

### Priority 3: Should-create in Q2

| # | File | Tests | Purpose | Effort |
|---|------|-------|---------|--------|
| 6 | `test_user_flows.py` | 4 | End-to-end user journeys | Medium-High |
| 7 | `test_css_selector_coverage.py` | 2 | CSS/wallet ID coverage audit | Low |

### Quick-Win: Cleanup existing tests

| # | File | Action | Impact |
|---|------|--------|--------|
| 1 | `test_worker_cancel_proper.py` | Currently 0 bytes — either implement tests or delete | Prevents confusion about test coverage |
| 2 | `test_error_handling.py` | Convert from print-based script to pytest tests | Integrates into CI |
| 3 | `test_final_functionality.py` | Convert from print-based script to pytest tests | Integrates into CI |
| 4 | `test_cpu_sleep.py:test_infinite_run` | Mark as skip (not xfail) — it tests manual Ctrl+C | Remove misleading xfail marker |
| 5 | `test_threading_ui_integration.py` | Add **one** test with real `run_worker` stub (not MagicMock) to catch Bug #2 | Transition toward integration |

---

## 7. Architectural Recommendations

### 7.1 Adopt `App.run_test()` Pattern

All 3 bugs were caused by testing in isolation from Textual's runtime. The test suite should migrate to using Textual's `App.run_test()` async context manager:

```python
from textual.app import App
from ui.app import WowFactorTUI

async def test_app_startup():
    async with App.run_test(WowFactorTUI()) as pilot:
        app = pilot.app
        assert app.current_screen is not None  # Bug #3 catch
```

This single pattern would catch all three bugs because:
- **Bug #1**: CSS is parsed during `App.run_test()` entry
- **Bug #2**: `run_worker` is the real Textual method, which validates its callable argument
- **Bug #3**: `current_screen` is a real Textual property, not a mock attribute

### 7.2 Reduce Mock Dependency

Currently ~60% of tests use `MagicMock` or `patch` to replace Textual infrastructure. The suite should:

1. **Classify tests** as "unit" (pure logic, OK to mock) vs "integration" (UI flow, use `App.run_test()`)
2. **Set a minimum of 20 integration tests** before the next milestone
3. **Remove `xfail` markers** from compose tests once they use `App.run_test()`

### 7.3 Conftest Cleanup

The session-scoped `initialize_navigation_manager` fixture in `conftest.py` that creates a `MockApp` with `current_screen = None` is a **false positive enabler**. Tests pass because the mock provides every attribute, regardless of whether the real App would have it.

**Recommendation:** Remove or deprecate the session-scoped nav initializer. Each integration test should initialize its own real app context.

### 7.4 Lint for Common Patterns

Add a pre-commit or CI check for:
- `MagicMock` usage on methods that should use real Textual APIs (`run_worker`, `compose`, `push_screen`)
- Tests that don't use `pytest` (print-based scripts in `test_error_handling.py`, `test_final_functionality.py`)
- Empty test files (`test_worker_cancel_proper.py`)

---

## 8. Summary Statistics

| Metric | Value |
|--------|-------|
| Total test files | 28 |
| Total passing tests | 313 |
| Tests with `xfail` markers | 34 |
| Tests with print-based scripts (non-pytest) | 3 |
| Empty test files | 1 |
| Tests using `App.run_test()` | 0 |
| Tests that mock `run_worker` | 4 |
| Tests that test CSS at runtime | 0 |
| Tests that test `current_screen` on real App | 0 |
| Tests that test button press sequences | 0 |
| Unit-level only tests | ~250 |
| Integration-level tests | 0 |
| **Coverage score (unit vs integration)** | **0% integration** |

**Bottom line:** The test suite is 313 tests of "does this class instantiate and does this function return the expected dict?" — it is not a test suite of "does the application work when a user runs it?" All 3 runtime bugs lived in the gap between those two worlds.