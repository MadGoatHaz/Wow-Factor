# DEV_LOG.md - GUI Rework Cycle COMPLETE

@@@ CURRENT_STATE @@@
All 16 chunks merged. 809 tests pass. GUI rework complete.

## branch/fix-profile-crash
- **Fix**: `main_menu.py` line 86 passed `profile_names=profile_names` to `ProfileSelectionScreen`, but `__init__` expects `profiles`. Changed to `profiles=profile_names`.
- **Fix**: `TrendsChartScreen._load_data_worker` and `AnalyticsScreen._load_data_worker` already `def` (sync) — no coroutine warning when run via `run_worker(thread=True)`.
- **Test**: Updated `test_load_data_worker_is_async` to `test_load_data_worker_is_sync` for both screen classes.
- 171 tests pass (navigation + integration + harness). App starts cleanly with no TypeError or RuntimeWarning.
- **Verification (2026-07-18)**: Re-confirmed both fixes hold. `timeout 5 python wowfactor.py` starts without crash. Full pytest suite passes. No TypeError on `ProfileSelectionScreen.__init__()` and no `RuntimeWarning` for coroutine.