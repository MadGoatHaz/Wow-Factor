# UI/UX Technical Manifest
## Screen-Based Architecture Audit Report

---

## 1. UI SCREEN HIERARCHY & RESPONSIBILITIES

### Entry Point
- **[`ui/app.py`](ui/app.py)** - Main application entry point, orchestrates screen navigation

### Core Screens (in `ui/screens/`)

| Screen File | Class Name | Primary Responsibility |
|-------------|------------|------------------------|
| [`main_menu.py`](ui/screens/main_menu.py:17) | `MainMenuScreen` | Main navigation hub - provides access to all major features via button-based menu |
| [`benchmark.py`](ui/screens/benchmark.py:63) | `RunSingleBenchmarkScreen` | Single CPU benchmark execution with duration/thread configuration |
| [`benchmark.py`](ui/screens/benchmark.py:259) | `RunBatchBenchmarkScreen` | Batch benchmark execution with cooldown management between runs |
| [`views.py`](ui/screens/views.py:34) | `ViewBestScoresScreen` | Display top-performing CPU scores per machine with export options |
| [`views.py`](ui/screens/views.py:366) | `CompareCPUScreen` | Side-by-side comparison of specific CPUs across benchmarks |
| [`views.py`](ui/screens/views.py:709) | `ViewAllScoresScreen` | Full historical score listing with pagination controls |
| [`analytics.py`](ui/screens/analytics.py:39) | `TrendsChartScreen` | Visual trend analysis charts for benchmark data over time |
| [`analytics.py`](ui/screens/analytics.py:181) | `AnalyticsScreen` | Analytics dashboard hub - routes to trends and other analytics views |
| [`cleanup.py`](ui/screens/cleanup.py:11) | `ClearInvalidScoresResultScreen` | Confirmation/result screen for removing invalid benchmark entries |

### Base Classes (in `ui/screens/`)
- **[`base_screen.py`](ui/screens/base_screen.py:65)** - `BaseScreen` - Abstract base class providing common services and initialization patterns
- **[`base_screen.py`](ui/screens/base_screen.py:13)** - `ScreenWithServices` - Mix-in for dependency injection of core services

### Shared Components (in `ui/`)
- **[`components.py`](ui/components.py)** - Reusable UI widgets including:
  - `WowFactorHeader` - Custom header component with gradient text
  - `DataTable` - Extended table widget with sorting/filtering capabilities
  - Export functionality integrated into screens via component methods
- **[`shared.py`](ui/shared.py)** - Shared utilities and constants across screens
- **[`messages.py`](ui/messages.py)** - Custom message classes for screen-to-screen communication

---

## 2. VISUAL DEBT ANALYSIS

### A. Inconsistent Color Usage
**Location:** Primarily [`components.py`](ui/components.py:76-290)

The CSS styling is embedded directly in Python code with scattered color definitions:

| Color | Hex Value | Usage Pattern |
|-------|-----------|---------------|
| Cyan (default text) | `#00FFFF` | Primary accent throughout |
| Magenta | `#FF00FF` | Borders, secondary accents |
| Dark Blue | `#000088` / `#000022` | Backgrounds - inconsistent variants used |
| Bright Blue | `#0000FF` | Alternative background - conflicts with dark blue |
| Yellow/Gold | `#FFFF00` / `#FFD700` | Metric labels, rankings |
| Green | `#00FF00` / `#39FF14` | Success states, values |
| Silver/Bronze | `#C0C0C0` / `#CD7F32` | Medal colors |

**Issues:**
- No centralized theme configuration - colors are hardcoded inline
- Multiple hex variants for similar purposes (e.g., two dark blue shades)
- Textual markup colors (`[yellow]`, `[green]`) mixed with CSS colors
- No color palette abstraction layer

### B. Layout Fragmentation
**Location:** [`components.py`](ui/components.py:86-290) and scattered across screens

CSS layout properties are distributed without consistent patterns:
```css
/* Example inconsistencies found */
width: 60%;           /* Used in multiple places */
width: 30;            /* Different unit style */
height: auto;         /* Common but inconsistent application */
max-height: 15;       /* Hardcoded pixel-like values */
margin: 1 0;          /* Shorthand - sometimes "0" used instead of "0 0" */
padding: 1;           /* Single value vs explicit padding */
```

**Issues:**
- No unified spacing system (no consistent margin/padding scale)
- Mix of percentage and absolute units without clear rationale
- Some components use `layout: grid` while others rely on default flow
- Width constraints vary wildly between similar component types

### C. Missing Visual Hierarchy
**Location:** Across all screen files

- No consistent header styling across screens
- Button variants (`primary`, `error`, `default`) used inconsistently
- Loading states only implemented in export functionality - missing from:
  - Benchmark execution screens
  - Data loading operations
  - Screen transitions

---

## 3. USABILITY DEBT ANALYSIS

### A. Navigation Patterns
**Location:** [`main_menu.py`](ui/screens/main_menu.py:44), [`views.py`](ui/screens/views.py:341,413)

Current navigation relies on hardcoded button IDs:
```python
# Example from main_menu.py:26-35
yield Button("Run New Benchmark", id="run_single_benchmark", variant="primary")
yield Button("View Best Score per Machine", id="view_best_scores", variant="primary")
yield Button("Compare a Specific CPU", id="compare_cpu", variant="primary")
```

**Issues:**
- No centralized navigation configuration - each screen defines its own buttons
- Button IDs are not consistent across screens (e.g., `back_to_main_menu` vs custom IDs)
- Keyboard shortcuts only partially implemented (pagination has `[Home]`, `[End]`, etc.)
- No breadcrumb trail or clear "current location" indicator
- Deep navigation paths possible without obvious return options

### B. Feedback Loop Gaps
**Location:** Scattered across [`components.py`](ui/components.py:317-354), [`benchmark.py`](ui/screens/benchmark.py)

| Feature | Status | Notes |
|---------|--------|-------|
| Loading states during benchmark | ✅ Implemented | Progress display with ops/sec |
| Loading states during export | ✅ Implemented | Static widget updates |
| Loading states for data views | ❌ Missing | No indication when loading scores |
| Error feedback consistency | ⚠️ Partial | Some use Static, some post messages |
| Success confirmation | ⚠️ Inconsistent | Varies by operation type |

**Issues:**
- Export errors show in different formats depending on error type
- Benchmark completion messages vary based on interruption status but lack visual distinction
- No toast/notification system for transient feedback
- Error messages sometimes logged but not shown to user

### C. Input Validation UX
**Location:** [`benchmark.py`](ui/screens/benchmark.py:526-551)

```python
# Example validation flow
duration_input_widget = self.query_one("#duration_input", Input)
# ... validation ...
self.query_one("#progress_display", Static).update("[red]Invalid duration...")
```

**Issues:**
- Validation errors displayed in progress display area - confusing placement
- No inline input validation feedback (errors appear after button press)
- Same error message format repeated across multiple validations
- No visual indication of which field has an error

### D. Data Display Issues
**Location:** [`views.py`](ui/screens/views.py:172-244)

Column width management is dynamic but inconsistent:
```python
table.add_column("Rank", key="rank", width=5)
table.add_column("CPU Model", key="cpu_model")  # No fixed width
```

**Issues:**
- Some columns have fixed widths, others are dynamic - causes layout shifts
- `_adjust_column_widths_and_wrap_names()` is a complex method that could be abstracted
- Long CPU names may still overflow despite wrapping logic
- No consistent sorting behavior across different views

---

## 4. CODE QUALITY & ARCHITECTURE ISSUES

### A. Styling Logic Concentration
**Primary Location:** [`components.py`](ui/components.py:76-290)

Approximately **215 lines** of CSS styling embedded directly in Python code:
- Lines 76-142: Component class definitions with inline styles
- Lines 143-185: DataTable and related component styles
- Lines 186-290+: Screen-specific widget styles

**Impact:**
- Makes styling changes difficult without understanding Python code structure
- No separation of concerns between UI logic and presentation
- Difficult to theme or skin the application

### B. Redundant Layout Calculations
**Location:** [`views.py`](ui/screens/views.py:214-244)

The `_adjust_column_widths_and_wrap_names()` method performs repeated width calculations:
```python
def _adjust_column_widths_and_wrap_names(self, table):
    max_widths = {}
    # Initialize with header widths
    for column_key in self.column_keys:
        max_widths[column_key] = len(str(column.label))
    # Check row data for maximum width
    for row_data in self.data:
        for key in self.column_keys:
            current_width = len(str(cell_value))
            max_widths[key] = max(max_widths[key], current_width)
```

**Impact:**
- O(n*m) complexity where n=rows, m=columns
- Could be optimized with a single pass or cached results
- Logic duplicated across different view implementations potentially

### C. Tight Coupling Between Screens and Components
**Location:** [`components.py`](ui/components.py:317-354)

Export functionality is tightly coupled:
```python
if self.query("DataTable"):  # Check if table exists in hierarchy
    self.query_one("#loading_display", Static).update(...)
```

**Impact:**
- Components assume specific screen structure (presence of `DataTable`, `#loading_display`)
- Makes components difficult to reuse in different contexts
- Creates fragile dependencies between layers

### D. Hardcoded Strings & Localization Readiness
**Location:** All screen files

Examples found:
```python
# main_menu.py:26-35 - Menu labels
"Run New Benchmark", "View Best Score per Machine"

# views.py:173-178 - Column headers
"Rank", "CPU Model", "Platform", "Threads"

# components.py:340, 344, 348 - Status messages
"Exported to {filename}", "Permission denied: {filename}"
```

**Impact:**
- No string externalization for localization
- Hardcoded UI text makes testing and maintenance harder
- No i18n infrastructure in place

---

## 5. RECOMMENDATIONS FOR ARCHITECT MODE

### Priority 1: Visual Theme Centralization
- Create a dedicated theme file (`ui/themes.py` or `ui/theme/`) with:
  - Color palette definitions as named constants
  - Spacing scale (margins, padding)
  - Typography settings
  - Component style templates

### Priority 2: Navigation Abstraction
- Implement a navigation service/hook that:
  - Centralizes screen transitions
  - Provides breadcrumb tracking
  - Manages keyboard shortcuts globally

### Priority 3: Feedback System Standardization
- Create a unified feedback mechanism:
  - Toast notifications for transient messages
  - Consistent error/success display patterns
  - Loading state indicators as reusable components

### Priority 4: Component Decoupling
- Refactor tightly-coupled components to:
  - Accept configuration via parameters rather than DOM queries
  - Provide clear interfaces for data injection
  - Separate presentation logic from business logic

---

## 6. FILE PATH SUMMARY FOR STYLING/LAYOUT LOGIC

| File | Line Range | Content Type |
|------|------------|--------------|
| [`ui/components.py`](ui/components.py:76-290) | ~76-290+ | CSS styling for all components |
| [`ui/screens/views.py`](ui/screens/views.py:172-244) | 172-244 | Table column width calculations |
| [`ui/screens/main_menu.py`](ui/screens/main_menu.py:26-35) | 26-35 | Button layout definitions |
| [`ui/screens/benchmark.py`](ui/screens/benchmark.py:78-84) | 78-84 | Benchmark screen button layout |

---

*Generated by Debug Mode UI/UX Audit*
