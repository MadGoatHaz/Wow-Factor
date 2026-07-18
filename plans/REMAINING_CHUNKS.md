# Remaining Chunks — Extraction from Blueprint & Roadmap

## I8: Fix 1 skipped test — `test_cpu_sleep.py`
- **Files to modify:** `tests/test_cpu_sleep.py`
- **Specific changes:** Either make the CPU sleep test run on all platforms, or mark it explicitly as `xfail` with a documented reason (OS-specific behavior).
- **Dependency classification:** ISOLATED — no dependencies.

## I9: Split `comprehensive_test_suite.py` into logical sub-files
- **Files to modify:** `tests/comprehensive_test_suite.py` (SOURCE — to be deleted), new files under `tests/`
- **Specific changes:** Decompose the 36,953-byte monolith test file. Each original test class moves into its own dedicated test file. Remove `comprehensive_test_suite.py` entirely after split.
- **Dependency classification:** ISOLATED — no dependencies.

## I10: Implement input validation layer for benchmark duration/thread inputs
- **Files to modify:** `ui/screens/benchmark.py` (or new validation module under `core/` or `ui/`)
- **Specific changes:** Add validation that duration > 0 and threads within `[1, cpu_count()]`. Invalid inputs must display inline validation errors to the user.
- **Dependency classification:** ISOLATED — no dependencies.

## I11: NOT DEFINED
- **Note:** The ROADMAP.md isolated tasks end at I-10. No I-11 exists in BUILD_BLUEPRINT.md or ROADMAP.md.

## I12: NOT DEFINED
- **Note:** The ROADMAP.md isolated tasks end at I-10. No I-12 exists in BUILD_BLUEPRINT.md or ROADMAP.md.

## C1: Add Type Hints to `core/benchmark.py`
- **Files to modify:** `core/benchmark.py`
- **Specific changes:** Add type hints to all functions and methods: `clean_cpu_model_name`, `get_cpu_info`, `format_large_number`, `_get_all_valid_scores`, `save_benchmark_results`, `_cpu_workload`, `execute_single_benchmark_run`, `get_best_score_per_machine`, `get_scores_for_cpu`, `get_unique_cpu_models`, `cleanup_invalid_scores`, `parse_date`, `is_date_in_range`, `get_unique_platforms`, `apply_all_filters`, `aggregate_scores_by_cpu`, `get_score_distribution`, `export_data_to_json`, `setup_logging`. Type-annotate `BenchmarkWorker` class (constructor, `run` method), `DependencyCache` class methods, and function-level `_monitor_cpu_freq` hints.
- **Verification:** `ruff check --select=ANN` passes.
- **Dependency classification:** Code Quality — no dependencies.