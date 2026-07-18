# EXECUTION PLAN — WowFactor
> Generated: 2026-07-18T09:02:44-06:00
> Source: Recon Architect post-timeout recovery

---

## BRANCH STATE

| Branch | Status | Notes |
|--------|--------|-------|
| `branch/i7` | ACTIVE, not merged | Only unstaged change: `logs/wowfactor.log` (untracked: `plans/STATUS.md`) |
| `master` | HEAD at `bea4dbc` | Merge branch 'branch/i5' — latest merged commit |

---

## CHUNKS DONE (merged to main)

| # | Chunk | Wave | Tests Added | Post-Merge Count |
|---|-------|------|-------------|------------------|
| 1 | CP1: Unify Theme Tokens With TCSS | Wave 1 | — | 536 passed, 4 skipped |
| 2 | CP2: Universal BaseScreen Adoption | Wave 1 | — | 536 passed, 4 skipped |
| 3 | CP3: Extract Shared Screens | Wave 1 | — | 536 passed, 4 skipped |
| 4 | I1: HomeScreen Rework | Wave 2 | +6 | 545 passed, 4 skipped |
| 5 | I2: Fix ViewBestScoresScreen Search | Wave 2 | +27 | 569 passed, 4 skipped |
| 6 | I3: Replace CPU Input with Dropdown | Wave 2 | +29 | 570 passed, 4 skipped |
| 7 | I4: Fix Benchmark Progress Bars | Wave 2 | +26 | 624 passed, 4 skipped |
| 8 | I6: Profile Creation Screen | Wave 2 | +43 | 667 passed, 4 skipped |
| 9 | I5: Footer Widget All Screens | Wave 3 | +53 | 667 passed, 4 skipped |

**Total tests collected today: 724** (up from 667 at last merge).

---

## CHUNKS PENDING (from ROADMAP.md)

### I-7 (ACTIVE — on branch/i7, NOT MERGED)
- **Task:** Write tests for `core/system_deps.py`
- **Effort:** 2-3h | **Dependencies:** None
- **Acceptance:** `tests/test_system_deps.py` with 8+ tests; gamemoded detection, package manager detection mocked

### I-8
- **Task:** Fix 1 skipped test — `test_cpu_sleep.py`
- **Effort:** 1h | **Dependencies:** None
- **Acceptance:** Either make test run on all platforms or mark explicitly as xfail with reason

### I-9
- **Task:** Split `comprehensive_test_suite.py` into logical sub-files
- **Effort:** 4-6h | **Dependencies:** None
- **Acceptance:** No mega-test file remains; each original test class in its own file

### I-10
- **Task:** Implement input validation layer for benchmark duration/thread inputs
- **Effort:** 2-3h | **Dependencies:** None
- **Acceptance:** Duration > 0, threads within [1, cpu_count()]; invalid inputs show inline validation errors

### CP-1
- **Task:** Verify and eliminate duplicate screen classes in `ui/components.py`
- **Effort:** 2-4h | **Dependencies:** None
- **Acceptance:** `grep -r "class.*Screen" ui/components.py` returns no screen class definitions

### CP-2
- **Task:** Implement dependency injection service registry
- **Effort:** 1-2d | **Dependencies:** CP-1
- **Acceptance:** `core/services/` with BenchmarkService, AnalyticsService, ConfigService protocols

### CP-3
- **Task:** Split `ui/screens/views.py` (765 lines) into dedicated modules
- **Effort:** 4-6h | **Dependencies:** CP-2
- **Acceptance:** Each file < 300 lines; `__init__.py` re-exports all classes

### CP-4
- **Task:** Implement targeted cache invalidation
- **Effort:** 1d | **Dependencies:** CP-2
- **Acceptance:** `BenchmarkCache.invalidate_dependents(key)` works; no nuclear invalidation

### C-1
- **Task:** Refactor `core/benchmark.py` (702 lines) — extract power management
- **Effort:** 6-8h | **Dependencies:** CP-1, CP-2
- **Acceptance:** `core/benchmark.py` < 500 lines; uses PowerService

### C-2
- **Task:** Refactor `core/analytics_engine.py` (552 lines) — split trend analysis
- **Effort:** 6-8h | **Dependencies:** CP-2
- **Acceptance:** `AnalyticsEngine` < 400 lines; `TrendEngine` handles regression

### C-3
- **Task:** Decouple `ui/screens/benchmark.py` (498 lines)
- **Effort:** 4-6h | **Dependencies:** CP-1, CP-2
- **Acceptance:** `benchmark.py` < 300 lines; batch logic in separate module

---

## RECOMMENDED PARALLEL EXECUTION ORDER

### Wave 3 — Immediate (all [ISOLATED], no dependencies)
These can run **simultaneously** in Agent Manager worktrees:

1. **I-7** (finish current branch/i7 work — tests for system_deps.py)
2. **I-8** (fix skipped test_cpu_sleep.py)
3. **I-9** (split comprehensive_test_suite.py)
4. **I-10** (input validation layer)

All four are independent. Fan out to 4 parallel Agent Manager sessions.

### Wave 4 — Foundation (after Wave 3 merges)
Sequential dependency chain:

5. **CP-1** (eliminate duplicate screens) → blocks CP-2
6. **CP-2** (DI service registry) → blocks CP-3, CP-4, C-1, C-2, C-3
7. **CP-3** + **CP-4** (can run in parallel after CP-2)

### Wave 5 — Core Refactoring
8. **C-1**, **C-2**, **C-3** (run in parallel after CP-2 merges)

---

## BRANCHES NEEDING REBASING

- **`branch/i7`**: Currently checked out, at `bea4dbc` (same as master HEAD). No rebase needed — it is already up-to-date with master. Just needs work committed and merged.

- **28 stale local branches** exist from pre-merge Wave 1/Wave 2 work (e.g., `branch/cp1-theme`, `branch/cp2-basescreen`, `branch/cp3-shared`, `branch/i1-home`, `branch/i2-runner`, `branch/i3-settings`, `branch/i4`, `branch/i5`, `branch/i6`). These can be pruned after Wave 3 completes.

---

## IMMEDIATE NEXT STEP

Complete I-7 on `branch/i7`: write `tests/test_system_deps.py` with 8+ tests covering gamemoded detection and package manager detection. Merge to master. Then fan out I-8, I-9, I-10 as parallel Agent Manager worktrees.