# Charts Implementation Plan for WowFactor TUI

## 1. Recommended Libraries
The current `requirements.txt` does not include any plotting libraries.

**Recommendation:** `textual-plotext`
*   **Why:** It is the standard wrapper for `plotext` within the Textual ecosystem, providing a native widget (`PlotextPlot`) that renders charts using characters (TUI-friendly). It handles resizing and integration with the Textual event loop automatically.
*   **Dependencies:** `textual-plotext` (which installs `plotext`).

## 2. UX Design: The "Analytics" Screen
Instead of cluttering the existing "View All Scores" list, we will introduce a dedicated **Analytics Screen**.

*   **Entry Point:** A new button "Analytics & Charts" on the Main Menu.
*   **Layout:**
    *   **Header:** Standard WowFactor Header ("ANALYTICS").
    *   **Navigation:** A `TabbedContent` widget to organize views:
        1.  **Tab 1: CPU Comparison:** Comparison of different processors.
        2.  **Tab 2: Trends:** Benchmark scores over time.
        3.  **Tab 3: Distribution:** Score distribution across all runs.
    *   **Footer:** Standard back/quit navigation.

## 3. Data Strategy
Data will be sourced from `wow_core.py`'s existing JSON loader. We will need new aggregation logic in `wow_core.py` to keep logic separate from UI.

*   **Metric 1: Average Ops/Sec by CPU (Comparison)**
    *   *Logic:* Group all valid scores by `system.processor_model`. Calculate the mean `ops_per_second`.
    *   *Chart:* Horizontal Bar Chart.
    *   *Axes:* Y-axis = CPU Model, X-axis = Average Score.
*   **Metric 2: Performance History (Trends)**
    *   *Logic:* Sort all scores by `timestamp`.
    *   *Chart:* Line Chart.
    *   *Axes:* X-axis = Date/Time, Y-axis = Ops/Sec.
    *   *Refinement:* Might need to limit to last N runs to ensure readability.
*   **Metric 3: Score Distribution**
    *   *Logic:* Create bins for score ranges (e.g., 0-10k, 10k-20k).
    *   *Chart:* Vertical Bar Chart (Histogram).
    *   *Axes:* X-axis = Score Range, Y-axis = Count of Runs.

## 4. Implementation Guide

### Step 1: Dependencies
Update `requirements.txt` and install:
```text
textual-plotext
```

### Step 2: Data Aggregation (Backend)
Modify `wow_core.py` to add helper functions:
*   `get_average_scores_by_cpu() -> Dict[str, float]` returns `{'Intel i7...': 15400.5, ...}`
*   `get_score_history(limit=50) -> Tuple[List[str], List[float]]` returns dates and scores.
*   `get_score_distribution() -> Tuple[List[str], List[int]]` returns bin labels and counts.

### Step 3: UI Components (Frontend)
Modify `ui/components.py`:
1.  Import `PlotextPlot` from `textual_plotext`.
2.  Define `AnalyticsScreen(Screen)`.
3.  Implement `compose()` using `TabbedContent`, `TabPane`, and `PlotextPlot` widgets.
4.  Implement `on_mount()` to fetch data and configure the plots:
    *   `plt.bar(cpus, scores)`
    *   `plt.theme('dark')` (or custom WowFactor colors)

### Step 4: Integration
1.  Add `AnalyticsScreen` to the `SCREENS` dictionary in `WowFactorTUI` app class.
2.  Add a button to `MainMenuScreen` to push the `AnalyticsScreen`.

### Step 5: Testing
*   Verify charts render correctly in the terminal.
*   Ensure resizing the window redraws charts.
*   Check handling of empty data states (e.g., "No benchmarks run yet" message instead of empty chart).