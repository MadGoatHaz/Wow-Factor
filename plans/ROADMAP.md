# WowFactor Strategic Roadmap — v1.1.1 → v2.0.0

**Generated:** 2026-07-12
**Current Version:** 1.1.0 (master, 4 commits)
**Analysis Scope:** All blueprints, architecture reviews, bugfix logs, and live test results

---

## 1. Current State Assessment

### What's Done ✅

| Area | Status | Evidence |
|------|--------|----------|
| **Documentation Consolidation** | COMPLETE | `README.md` clean, `docs/BUGFIX_SUMMARY.md`, `docs/UI_UX_AUDIT_MANIFEST.md` exist |
| **Project Cleanup** | COMPLETE | Legacy `.txt` files removed, `data/` directory structured, `benchmark_results/` organized |
| **Screen Architecture** | PARTIALLY COMPLETE | `ui/screens/` split (10 files), but `ui/components.py` may still contain duplicate screen classes |
| **Worker Error Fixes** | COMPLETE | All 3 WorkerError root causes resolved (sync/async invocation, WorkerCancelled import) |
| **ColumnKey / ValueError Bugfixes** | COMPLETE | 6 critical UI crashes resolved (compare CPU, column widths, CSV export headers) |
| **Test Suite Expansion** | COMPLETE | 21 test files, 212 passed, 1 skipped — Phase 2 test gap blueprint fully implemented |
| **Power Management** | COMPLETE | `core/power.py` with GameMode integration and CPU governor switching |
| **Export Functionality** | COMPLETE | CSV/JSON/XML/YAML exporters tested and verified |
| **Config Management** | COMPLETE | `ConfigManager` with JSON persistence, benchmark profiles |
| **Exception Hierarchy** | COMPLETE | `core/exceptions.py` defines custom error classes |

### What's Broken / Incomplete ⚠️

| Issue | Severity | Source |
|-------|----------|--------|
| **Duplicate screen classes may exist** | HIGH | `ARCHITECTURE_REVIEW_REPORT.md` C1 — `ui/components.py` vs `ui/screens/benchmark.py` |
| **Tight UI-to-core coupling** | HIGH | `ARCHITECTURE_REVIEW_REPORT.md` M1, `PHASE2_MASTER_BLUEPRINT.md` 1.2 |
| **No dependency injection** | HIGH | All screens import core functions directly — untestable in isolation |
| **Global state (config_manager singleton)** | MEDIUM | `core/config.py:232` — hidden dependencies |
| **Cache invalidation is nuclear** | MEDIUM | `_invalidate_all_cache()` used everywhere vs targeted invalidation |
| **`ui/screens/views.py` at 765 lines** | HIGH | Exceeds 500-line maintainability threshold |
| **`core/benchmark.py` at 702 lines** | HIGH | Same threshold |
| **`ui/screens/analytics.py` at 544 lines** | MEDIUM-HIGH | Approaching threshold |
| **Missing type hints** | LOW | Inconsistent annotation coverage across codebase |
| **Windows power management placeholder** | LOW | `core/power.py:181-192` |
| **No structured logging** | LOW | All logging is ad-hoc print/debug |
| **No config schema validation** | MEDIUM | JSON loaded without validation |
| **Input validation gaps** | MEDIUM | Profile names unsanitized, no batch run count limits |
| **No theme centralization** | MEDIUM | Hardcoded hex colors scattered across `ui/components.py` |
| **No navigation abstraction** | LOW | Button IDs hardcoded per-screen |

### What's NOT Started 🔲

- Dependency injection service registry
- Cache dependency tracking system
- Screen extraction from `ui/components.py` (if duplicates exist)
- UI/UX improvements (theme file, navigation service, unified feedback system)
- Data visualization enhancements (JSON export, advanced charts)
- Keyboard shortcuts and advanced search/filtering
- Performance profiling of large datasets (>10k entries)
- Pre-commit hooks integration (config file exists but not installed)

---

## 2. Test Results Summary

```
Total:     213 collected
Passed:    212
Skipped:    1  (test_cpu_sleep.py — expected, OS-specific)
Failed:     0
Duration:  83.37s
```

### Test Coverage Breakdown

| Test File | Tests | Module Coverage |
|-----------|-------|-----------------|
| `test_aggregation.py` | 9 | Data aggregation functions |
| `test_analytics_engine.py` | 54 | `core/analytics_engine.py` (35 initial + 19 additional) |
| `test_benchmark_worker.py` | 36 | Worker processes, dependency cache, cooldown |
| `test_charts_ui.py` | 1 | Chart rendering |
| `test_comparator.py` | 10 | `core/comparator.py` |
| `test_config_manager.py` | 11 | `core/config.py` |
| `test_cpu_sleep.py` | 1/0 | OS-specific, skipped |
| `test_error_handling.py` | 1 | Global error handling |
| `test_export_formats.py` | 8 | Export format generation |
| `test_export_functionality.py` | 3 | Export integration |
| `test_export_improvements.py` | 1 | Export enhancements |
| `test_exporters.py` | 54 | `core/exporters.py` (all 4 exporters + edge cases) |
| `test_final_functionality.py` | 6 | End-to-end functional tests |
| `test_loading_states.py` | 1 | UI loading states |
| `test_pagination.py` | 3 | View pagination |
| `test_power_management.py` | 4 | `core/power.py` |
| `test_threading_logic.py` | 3 | Worker threading patterns |
| `test_threading_ui_integration.py` | 5 | UI-thread integration |
| `test_worker_cancel.py` | 1 | Worker cancellation |
| `test_worker_integration.py` | 1 | Worker lifecycle |
| `comprehensive_test_suite.py` | included | Mega-test file (36,953 bytes) |

### Test Quality Observations

- **Strength:** `test_exporters.py` and `test_analytics_engine.py` are comprehensive (54 tests each)
- **Weakness:** `test_charts_ui.py` has only 1 test despite `textual_plotext` integration
- **Weakness:** `test_error_handling.py` has only 1 test despite `ARCHITECTURE_REVIEW_REPORT.md` flagging H1
- **Risk:** `comprehensive_test_suite.py` (36KB) is a monolith — should be split into logical groups
- **Coverage gap:** No tests for `ui/screens/profile_selection.py`, `ui/screens/cleanup.py`, `ui/navigation.py`, `ui/notifications.py`, `ui/layout_utils.py`, `ui/shared.py`, `ui/theme.py`, `core/system_deps.py`
- **Coverage gap:** No tests for the main entry point `wowfactor.py` venv logic

---

## 3. Priority-Ordered Development Backlog

### [CRITICAL-PATH] — Blocking future development

| # | Task | Effort | Dependencies | Acceptance Criteria |
|---|------|--------|--------------|---------------------|
| CP-1 | Verify and eliminate duplicate screen classes in `ui/components.py` | 2-4h | None | `grep -r "class.*Screen" ui/components.py` returns no screen class definitions; all screens live exclusively in `ui/screens/` |
| CP-2 | Implement dependency injection service registry | 1-2d | CP-1 | `core/services/` directory with `BenchmarkService`, `AnalyticsService`, `ConfigService` protocols; screens receive services via constructor or property; all existing tests still pass |
| CP-3 | Split `ui/screens/views.py` (765 lines) into `views_best.py`, `views_compare.py`, `views_all.py` | 4-6h | CP-2 | Each new file < 300 lines; `ui/screens/__init__.py` re-exports all classes; all existing tests pass |
| CP-4 | Implement targeted cache invalidation | 1d | CP-2 | `BenchmarkCache.invalidate_dependents(key)` works; `_invalidate_all_cache()` calls targeted version; no stale data in visual regression tests |

### [COUPLED-TO: CP-1] — Depends on screen extraction

| # | Task | Effort | Dependencies | Acceptance Criteria |
|---|------|--------|--------------|---------------------|
| C-1 | Refactor `core/benchmark.py` (702 lines) — extract power management calls to dedicated service | 6-8h | CP-1, CP-2 | `core/benchmark.py` < 500 lines; `execute_single_benchmark_run()` uses `PowerService` instead of direct `PowerPlanManager` import |
| C-2 | Refactor `core/analytics_engine.py` (552 lines) — split trend analysis into `TrendEngine` | 6-8h | CP-2 | `AnalyticsEngine` < 400 lines; `TrendEngine` handles linear regression; existing analytics tests pass |
| C-3 | Decouple `ui/screens/benchmark.py` (498 lines) — extract batch logic to `BatchBenchmarkEngine` | 4-6h | CP-1, CP-2 | `benchmark.py` < 300 lines; batch worker logic in separate module; all threading tests pass |

### [ISOLATED] — Independent work, can run in parallel

| # | Task | Effort | Dependencies | Acceptance Criteria |
|---|------|--------|--------------|---------------------|
| I-1 | Add type hints to `core/config.py` and `core/comparator.py` | 2-3h | None | `mypy core/config.py core/comparator.py` passes with zero errors; `pyproject.toml` mypy config verified |
| I-2 | Add structured logging (`logging` module) to all `core/` modules | 3-4h | None | Each `core/` module uses `logger = logging.getLogger(__name__)`; log level configurable via env var `WOFACTOR_LOG_LEVEL` |
| I-3 | Implement JSON schema validation for `ConfigManager` | 4-6h | None | `pydantic` or `jsonschema` validates `defaults.json` and `benchmark_profiles.json` on load; invalid configs produce clear error messages |
| I-4 | Write tests for `ui/navigation.py` (104 lines) | 3-4h | None | `tests/test_navigation.py` with 15+ tests; `NavigationManager` singleton reset works in test teardown |
| I-5 | Write tests for `ui/notifications.py` | 2-3h | None | `tests/test_notifications.py` with 10+ tests; toast dismiss lifecycle covered |
| I-6 | Write tests for `wowfactor.py` entry point | 3-4h | None | `tests/test_venv_management.py` with 10+ tests; venv creation, dependency install, OS detection mocked |
| I-7 | Write tests for `core/system_deps.py` | 2-3h | None | `tests/test_system_deps.py` with 8+ tests; gamemoded detection, package manager detection mocked |
| I-8 | Fix 1 skipped test — `test_cpu_sleep.py` | 1h | None | Either make test run on all platforms or mark explicitly as xfail with reason |
| I-9 | Split `comprehensive_test_suite.py` into logical sub-files | 4-6h | None | No mega-test file remains; each original test class in its own file |
| I-10 | Implement input validation layer for benchmark duration/thread inputs | 2-3h | None | Duration > 0, threads within `[1, cpu_count()]`; invalid inputs show inline validation errors |

### [ENHANCEMENT] — Nice-to-have, low risk

| # | Task | Effort | Dependencies | Acceptance Criteria |
|---|------|--------|--------------|---------------------|
| E-1 | Create centralized `ui/theme.py` with color palette and spacing scale | 4-6h | None | All hardcoded hex colors replaced with theme constants; no visual regression |
| E-2 | Implement keyboard shortcuts (global nav, pagination, search) | 3-4h | E-1 | `Q` quit, `B` benchmark, `V` view scores, `A` analytics, `C` compare from any screen |
| E-3 | Implement Windows power management in `core/power.py` | 4-6h | None | `power.exe` or `powercfg` commands on Windows; `PowerPlanManager` works cross-platform |
| E-4 | Add JSON export to Analytics screen | 3-4h | None | Analytics screen has JSON export button; produces valid JSON file |
| E-5 | Improve `test_charts_ui.py` from 1 test to 10+ | 2-3h | None | Mock textual_plotext; test chart data preparation, scaling, rendering pipeline |
| E-6 | Create `docs/ARCHITECTURE.md` from this roadmap's reference architecture | 2-3h | None | Updated diagram reflects current `ui/screens/` structure; data flow for benchmark, analytics, export documented |
| E-7 | Implement pre-commit hooks (`ruff check`, `ruff format`, `pytest`) | 1h | None | `pre-commit install` works; `git commit` runs linter + tests on staged files |
| E-8 | Performance benchmark with >10k score entries | 2-3h | None | `core/benchmark.py` data loading completes < 2s with 10k entries; pagination works correctly |
| E-9 | Add search/filter to analytics screen | 4-6h | None | Filter by date range, CPU model, min score; analytics results update in real-time |
| E-10 | Extract reusable widgets from `ui/components.py` to `ui/components/widgets.py` | 4-6h | E-1 | `WowFactorHeader` and `DataTable` in dedicated module; component tests pass |

---

## 4. Dependency Mapping

```
                    [START]
                       │
                CP-1: Eliminate duplicates
                       │
              ┌────────┼────────┐
              │        │        │
           CP-2      CP-3     I-8
           DI       Split     Fix skip
           Registry  views.py  test
              │
        ┌─────┼─────┐
        │     │     │
      C-1   C-2   C-3   I-1  I-2  I-3  I-4  I-5  I-6  I-7  I-9
   benchmark  analytics  batch  Type  Log  Schema  Nav  Notif  Venv  SysDeps  Split
    refactor  refactor  refactor hints                       tests    tests
        │     │     │
        └─────┼─────┘
              │
            CP-4
         Cache
         invalidation
              │
              ▼
          [PHASE-2 BASELINE REACHED]
              │
        ┌─────┼────────────────┐
        │     │                │
      E-1   E-3           E-10
     Theme  Windows      Widget
           Power        Extraction
        ┌───┼───┐
        │   │   │
      E-2  E-4 E-5  I-10  E-6  E-7  E-8  E-9
    Shortcuts JSON   Chart  Arch  Pre    Large  Search
             Export  tests  Doc   Comm   Data   Filter
```

---

## 5. Recommended Implementation Order

### Phase A: Foundation Stabilization (Week 1)
**Goal:** Clean up duplication, establish testability patterns

| Order | Task | Rationale |
|-------|------|-----------|
| 1 | **CP-1** — Eliminate duplicate screen classes | Removes technical debt that blocks all other work |
| 2 | **CP-3** — Split `views.py` (765 → 3 × ~250) | Largest file first; reduces merge conflict risk |
| 3 | **CP-2** — Dependency injection service registry | Enables testability for all subsequent refactoring |
| 4 | **CP-4** — Targeted cache invalidation | Eliminates nuclear invalidation before code moves around it |
| 5 | **All [ISOLATED]** tasks (I-1 through I-9) | Run in parallel; no cross-dependencies |
| 6 | Verify: `pytest` passes 212/213, `ruff check` clean | Gate before Phase B |

### Phase B: Core Refactoring (Week 2-3)
**Goal:** Decompose monolithic core files

| Order | Task | Rationale |
|-------|------|-----------|
| 1 | **C-1** — Refactor `core/benchmark.py` | Most dependencies; foundation for everything else |
| 2 | **C-2** — Refactor `core/analytics_engine.py` | After benchmark service is stable |
| 3 | **C-3** — Refactor `ui/screens/benchmark.py` | After core benchmark service is decoupled |
| 4 | Verify: `pytest` passes, manual benchmark test | Gate before Phase C |

### Phase C: Polish & Enhancement (Week 4+)
**Goal:** UX improvements, cross-platform, documentation

| Order | Task | Rationale |
|-------|------|-----------|
| 1 | **E-1** — Centralize theme | Reduces visual debt across all screens |
| 2 | **E-10** — Extract reusable widgets | Benefits from new theme system |
| 3 | **E-3** — Windows power management | Independent of UI work |
| 4 | **E-2** — Keyboard shortcuts | Built on stable navigation |
| 5 | **E-6** — Architecture documentation | Document the new structure |
| 6 | **E-4, E-5, E-8, E-9** — Feature enhancements | In any order, all independent |
| 7 | **I-10** — Input validation layer | Security hardening |
| 8 | **E-7** — Pre-commit hooks | Final hygiene |
| 9 | Verify: Full test suite + manual QA on all screens | Final gate |

---

## 6. Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| DI breaks existing screen imports | HIGH | MEDIUM | Keep backward-compatible re-exports in `ui/__init__.py` during transition |
| Benchmark worker tests fail after refactoring | MEDIUM | HIGH | Freeze `test_benchmark_worker.py` snapshot before C-1; compare after |
| Cache refactoring causes stale data | MEDIUM | HIGH | Run `test_aggregation.py` and `test_final_functionality.py` as canary |
| Views.py split causes merge conflicts | LOW | MEDIUM | Isolate to one PR; run full test suite immediately |
| DI adds complexity without benefit | MEDIUM | LOW | Use minimal DI (service properties) rather than full IoC container |

---

## 7. Success Criteria for v2.0.0

1. **All screen files < 500 lines** (current: 3 files exceed this)
2. **212+ tests passing** (maintain current count or higher)
3. **Zero duplicate screen class definitions**
4. **All core modules have type hints** (mypy clean)
5. **Dependency injection in place** — screens use service protocols
6. **Targeted cache invalidation** — no `_invalidate_all_cache()` calls
7. **All 8 core modules have structured logging**
8. **Config schema validation** — invalid configs rejected with clear errors
9. **Cross-platform power management** (Linux + Windows)
10. **All existing functionality preserved** — no feature regression

---

## 8. Deprecated / Superseded Plans

| Superseded File | Reason | Action |
|-----------------|--------|--------|
| `MASTER_BLUEPRINT.md` | Phase 1 complete; architecture evolved | Archive in `docs/archive/` |
| `PHASE2_MASTER_BLUEPRINT.md` | Implementation started; partial completion | Superseded by this roadmap |
| `PHASE2_TEST_GAP_BLUEPRINT.md` | All 7 test files implemented (212 tests) | Mark complete; no further action needed |
| `PHASE3_WORKER_FIX_BLUEPRINT.md` | All 3 worker issues resolved | Mark complete; no further action needed |
| `ARCHITECTURE_REVIEW_REPORT.md` | Issues tracked in backlog | Update with verification notes as items close |
| `docs/BUGFIX_SUMMARY.md` | Bugs resolved | Archive; migrate unresolved items to backlog |
| `docs/UI_UX_AUDIT_MANIFEST.md` | UI issues tracked as E-1 through E-10 | Superseded by Phase C items |

---

*End of Roadmap.*