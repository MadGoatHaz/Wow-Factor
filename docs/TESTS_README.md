# WowFactor TUI Test Suite Documentation

## Overview
This document provides an inventory of all test files, their functions, and execution instructions.

## Test File Inventory

| File | Purpose | Key Tests |
|------|---------|-----------|
| `tests/test_config_manager.py` | Configuration loading/saving | Config creation, persistence, validation (11 tests) |
| `tests/test_export_formats.py` | Export functionality (XML/YAML) | Format generation, file writing (8 tests) |
| `tests/test_threading_logic.py` | Benchmark worker threading | Thread safety, progress reporting (3 tests - FAILING) |
| `tests/test_worker_integration.py` | Worker class integration | Single/batch benchmark execution (1 test - FAILING) |
| `tests/test_charts_ui.py` | UI chart rendering | Analytics/Trends screens |
| `tests/test_loading_states.py` | Loading overlay behavior | State transitions |
| `tests/test_pagination.py` | Data pagination logic | Page navigation, data slicing |
| `tests/test_comparator.py` | CPU comparison engine | Benchmark result comparison (9 tests) |
| `tests/test_aggregation.py` | Score aggregation logic | Best score calculation (8 tests) |
| `tests/test_power_management.py` | Power plan handling | Windows/Linux compatibility |
| `tests/test_cpu_sleep.py` | Cooldown/sleep functionality | Timing accuracy |
| `tests/test_error_handling.py` | Exception handling coverage | Error scenarios |
| `tests/test_final_functionality.py` | End-to-end flows | Complete user journeys (6 tests) |
| `tests/comprehensive_test_suite.py` | Full integration testing | All components |
| `tests/test_export_functionality.py` | Export UI flows | View/export best scores, compare CPU (3 tests) |
| `tests/test_export_improvements.py` | CSV exporter implementation | CSV export functionality (1 test) |
| `tests/test_threading_ui_integration.py` | Threading + UI integration | Validation, completion handlers (5 tests - FAILING) |
| `tests/test_worker_cancel.py` | Worker cancellation logic | Cancel benchmark execution |

## Execution Instructions

### Run Full Suite
```bash
python -m pytest tests/ -v --tb=short
```

### Run Specific Test File
```bash
python -m pytest tests/test_config_manager.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=. --cov-report=html
```

### Skip Failing Tests (Threading Issues)
```bash
python -m pytest tests/ -v --tb=short --ignore=tests/test_threading_logic.py --ignore=tests/test_worker_integration.py --ignore=tests/test_threading_ui_integration.py
```

## Recent Changes (Phase 5 Restructuring)

- **Import Chain Restructured:** All screen imports now use canonical `ui.screens.*` paths
- **Duplicate Screens Removed:** `MainMenuScreen`, `RunSingleBenchmarkScreen`, `RunBatchBenchmarkScreen`, `ClearInvalidScoresResultScreen` consolidated to `ui/screens/*` modules
- **Exception Handling Fixed:** Bare `except:` clauses replaced with `except Exception:` in test files
- **Test Files Updated:** 6 test files had imports updated to reflect new screen locations

## Verification Status (Phase 5 Final)

| Check | Status | Details |
|-------|--------|---------|
| Import chain resolution | PASS | `import wowfactor` successful |
| Screen consolidation | PASS | Only `LoadingOverlay` remains in `ui/components.py` |
| Exception handling hygiene | PASS | No bare `except:` in project code (only 3rd-party deps) |
| Application launch | PASS | TUI renders main menu correctly |
| Test suite execution | PARTIAL | **60 passed, 9 failed, 1 skipped** |

### Failing Tests Summary

| Test File | Failed Tests | Root Cause |
|-----------|--------------|------------|
| `test_threading_logic.py` (3 failures) | `test_single_threaded_execution`, `test_multi_threaded_execution`, `test_result_structure_with_threads` | `RuntimeError: Queue objects should only be shared between processes through inheritance` - multiprocessing queue serialization issue in [`core/benchmark.py`](core/benchmark.py:360) |
| `test_worker_integration.py` (1 failure) | `test_basic_functionality` | Same multiprocessing queue serialization error |
| `test_threading_ui_integration.py` (5 failures) | All validation and completion tests | `RuntimeError: NavigationManager not initialized. Call initialize() first.` - test setup missing app initialization |

## Test Results Summary

```
=========================== short test summary info ============================
FAILED tests/test_threading_logic.py::test_single_threaded_execution
FAILED tests/test_threading_logic.py::test_multi_threaded_execution  
FAILED tests/test_threading_logic.py::test_result_structure_with_threads
FAILED tests/test_threading_ui_integration.py::TestThreadingUIIntegration::test_on_benchmark_completion_success
FAILED tests/test_threading_ui_integration.py::TestThreadingUIIntegration::test_start_benchmark_validation_invalid_threads
FAILED tests/test_threading_ui_integration.py::TestThreadingUIIntegration::test_start_benchmark_validation_max_threads_warning
FAILED tests/test_threading_ui_integration.py::TestThreadingUIIntegration::test_start_benchmark_validation_non_integer_threads
FAILED tests/test_threading_ui_integration.py::TestThreadingUIIntegration::test_start_benchmark_validation_valid
FAILED tests/test_worker_integration.py::test_basic_functionality
=================== 9 failed, 60 passed, 1 skipped in 35.97s ===================
```

## Remediation Recommendations

### Issue 1: Multiprocessing Queue Serialization
**Location:** [`core/benchmark.py`](core/benchmark.py:347-362)  
**Fix Strategy:** Pass queue via process inheritance (child process creation) rather than as function argument. Use `multiprocessing.Process` with queue passed at spawn time, or refactor to use callbacks/IPC mechanisms that support serialization.

### Issue 2: NavigationManager Initialization in Tests
**Location:** [`tests/test_threading_ui_integration.py`](tests/test_threading_ui_integration.py:57-102)  
**Fix Strategy:** Add proper test setup with `@pytest.fixture` that initializes `NavigationManager` and mocks app context before screen instantiation.

---
*Last Updated: Phase 5 Final Verification (2026-04-15)*
