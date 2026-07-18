# DEV_LOG.md - GUI Rework Cycle COMPLETE

@@@ CURRENT_STATE @@@
All 16 chunks merged. 809 tests pass. GUI rework complete. TrendsChart and AnalyticsScreen test fixes applied.

## branch/fix-profile-crash
- **Fix**: `ProfileSelectionScreen.__init__` now accepts `profiles=None` (default) so navigation with `create_new=True` no longer crashes
- **Fix**: `TrendsChartScreen._load_data_worker` and `AnalyticsScreen._load_data_worker` changed from `async def` to `def` — eliminates `RuntimeWarning: coroutine was never awaited` when run via `run_worker(thread=True)`
- **Test**: Updated `test_load_data_worker_is_async` to `test_load_data_worker_is_sync` for both screen classes
- 152 tests pass. App starts cleanly with no TypeError or RuntimeWarning.

## branch/fix-trends-analytics
- **Fix**: `get_score_distribution()` in `core/benchmark.py` replaced unbounded linear binning (caused 136M bins from 68B outlier score) with fixed 20-bin percentile-based histogram — eliminates infinite loop in AnalyticsScreen test
- **Fix**: `TrendsChartScreen._update_cpu_tabs()` migrated from `tabbed_content._panes` (removed in Textual 8.x) to `walk_children(TabPane)` + `remove_pane(pane_id)` API
- **Fix**: `TrendsChartScreen._update_cpu_tabs()` migrated `add_pane(label, widget)` to `add_pane(TabPane(label, widget))` for Textual 8.x compatibility
- **Fix**: CPU model tab IDs sanitized with `re.sub(r'[^a-zA-Z0-9_-]', '_', name)` to produce valid CSS identifiers (e.g., "Snapdragon (TM) 8cx" → "Snapdragon__TM__8cx")
- 3 tests pass: `test_charts_ui.py`, `test_trends_chart_compose`, `test_analytics_compose`