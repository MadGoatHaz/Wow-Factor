"""
Analytics screens module - Contains AnalyticsScreen and TrendsChartScreen.

These screens provide visualization capabilities for benchmark data:
- TrendsChartScreen: Displays benchmark score trends over time using line charts
- AnalyticsScreen: Provides analytics dashboard with bar charts, distribution plots, and correlation scatter plots
"""
from typing import Dict, List
import logging
from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static, Button, Footer
from textual.binding import Binding
from textual.message import Message

from .base_screen import ScreenWithServices, BaseScreen
# Import shared components to avoid circular imports
from ui.shared import WowFactorHeader, RETRO_GRADIENT_COLORS, colorize_text_gradient

# Import remaining components directly
from textual.widgets import TabbedContent, TabPane
from textual_plotext import PlotextPlot
from core.benchmark import _get_all_valid_scores, aggregate_scores_by_cpu, get_score_distribution
from core.analytics_engine import AnalyticsEngine


def convert_timestamp_to_unix(timestamp_str: str) -> float:
    """
    Convert ISO-format timestamp string to Unix timestamp.
    
    Handles format: 'YYYY-MM-DD HH:MM:SS'
    Returns Unix timestamp as float for compatibility with plotext.
    """
    if not timestamp_str:
        return 0.0
    try:
        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        return dt.timestamp()
    except ValueError:
        # Fallback: return 0 if parsing fails
        return 0.0

class DataLoadComplete(Message):
    """Message indicating data loading completed successfully."""
    def __init__(self, data: List[Dict]) -> None:
        super().__init__()
        self.data = data


class DataLoadError(Message):
    """Message indicating data loading failed."""
    pass


class TrendsChartScreen(BaseScreen):
    """
    Screen for displaying benchmark score trends over time using line charts.
    Shows how scores have changed across multiple runs for each CPU.
    """
    BINDINGS = [
        ("b", "go_back", "Back to Main Menu"),
        ("q", "quit_app", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Container():
            yield WowFactorHeader(id="app-header")
            yield Static(colorize_text_gradient("BENCHMARK TRENDS OVER TIME", RETRO_GRADIENT_COLORS), classes="title compact-header")
            
            # Create tabs for each CPU that has been benchmarked
            with TabbedContent(classes="analytics-container"):
                # Default tab showing all CPUs combined
                with TabPane("All CPUs Combined"):
                    yield PlotextPlot(id="all_cpus_plot")
                
                # Dynamic tabs will be added here for each CPU
                # We'll use a placeholder that gets replaced dynamically
                with TabPane("Loading..."):
                    yield PlotextPlot(id="cpu_specific_plot")
            
            with Horizontal(classes="action-buttons compact-button"):
                yield Button("Back", id="back_to_main_menu", variant="default", classes="action-btn")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#app-header", WowFactorHeader).update_title("TRENDS CHART")
        self.load_data()

    def load_data(self) -> None:
        """Load benchmark data and prepare for chart rendering."""
        self.run_worker(lambda: self._load_data_worker(), thread=True, group="data_loading")

    def _load_data_worker(self):
        """Worker function to load all valid scores from disk."""
        try:
            all_scores = _get_all_valid_scores()
            self.post_message(DataLoadComplete(all_scores))
        except Exception as e:
            logging.error(f"Error loading trends data: {e}")
            self.post_message(DataLoadError())

    def on_data_load_complete(self, message: DataLoadComplete) -> None:
        """Handle completed data load and render charts."""
        self.all_scores = message.data
        self.render_charts()

    def on_data_load_error(self, message: DataLoadError) -> None:
        """Handle data loading errors."""
        self.navigation.notify("Error loading trends data. Please try again.", type="error")

    def render_charts(self) -> None:
        """Render line charts showing trends over time for each CPU."""
        if not hasattr(self, 'all_scores') or not self.all_scores:
            # No data available
            all_plot = self.query_one("#all_cpus_plot", PlotextPlot)
            all_plot.plt.clear_data()
            all_plot.plt.title("No Data Available")
            all_plot.refresh()
            return
        
        # Group scores by CPU model and sort by timestamp
        cpu_scores_by_time: Dict[str, List[Dict]] = {}
        for score in self.all_scores:
            cpu_model = score.get('system', {}).get('processor_model', 'Unknown')
            if cpu_model not in cpu_scores_by_time:
                cpu_scores_by_time[cpu_model] = []
            cpu_scores_by_time[cpu_model].append(score)
        
        # Sort each CPU's scores by timestamp
        for cpu_model in cpu_scores_by_time:
            cpu_scores_by_time[cpu_model].sort(key=lambda x: x.get('timestamp', ''))
        
        # Render "All CPUs Combined" chart - shows all data points together
        all_plot = self.query_one("#all_cpus_plot", PlotextPlot)
        all_plot.plt.clear_data()
        
        if cpu_scores_by_time:
            # Collect all timestamps and scores for combined view
            all_timestamps = []
            all_scores_list = []
            for cpu_model, scores in cpu_scores_by_time.items():
                for score in scores:
                    ts = score.get('timestamp', '')
                    all_timestamps.append(convert_timestamp_to_unix(ts))
                    all_scores_list.append(score.get('ops_per_second', 0))
            
            if all_timestamps and all_scores_list:
                # Sort by Unix timestamp
                combined = sorted(zip(all_timestamps, all_scores_list), key=lambda x: x[0])
                all_timestamps, all_scores_list = zip(*combined)
                
                all_plot.plt.plot(list(all_timestamps), list(all_scores_list), color='cyan', marker='dot')
                all_plot.plt.title("All Benchmark Runs Over Time")
                all_plot.plt.xlabel("Timestamp")
                all_plot.plt.ylabel("Score (Ops/Second)")
                all_plot.plt.grid(True)
        else:
            all_plot.plt.title("No Data Available")
        
        all_plot.refresh()
        
        # Update the CPU-specific tab with actual CPU tabs
        self._update_cpu_tabs(cpu_scores_by_time)
    
    def _update_cpu_tabs(self, cpu_scores_by_time: Dict[str, List[Dict]]) -> None:
        """Update the TabbedContent to show individual CPU trend charts."""
        tabbed_content = self.query_one(TabbedContent)

        # Save current active tab ID to restore after removal
        saved_active = tabbed_content.active or ""

        # Remove all tabs except the first one (All CPUs Combined) by pane ID
        # In Textual 8.x, remove_pane requires a pane_id string, not an index
        to_remove = []
        for child in tabbed_content.walk_children(TabPane):
            if child.id and child.id != "all_cpus_plot":
                to_remove.append(child.id)
        for pane_id in to_remove:
            tabbed_content.remove_pane(pane_id)

        # Restore active tab
        tabbed_content.active = saved_active

        # Add a tab for each CPU
        for cpu_model, scores in cpu_scores_by_time.items():
            if not scores:
                continue

            # Sanitize CPU model name to create a valid CSS identifier
            import re
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', cpu_model)
            tab_id = f"cpu_plot_{safe_name}"
            pane = TabPane(cpu_model[:50], PlotextPlot(id=tab_id))
            tabbed_content.add_pane(pane)

        # Refresh the tabbed content to show new tabs
        tabbed_content.refresh()
    
    def action_go_back(self) -> None:
        """Navigate back to main menu."""
        self.navigation.go_back()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "back_to_main_menu":
            self.action_go_back()
            event.stop()
        elif event.button.id == "quit_app":
            self.app.exit()
            event.stop()


class AnalyticsScreen(BaseScreen):
    """
    Screen for displaying analytics dashboard with various chart types.
    Includes CPU average scores, score distribution, and correlation analysis.
    """
    BINDINGS = [
        ("b", "go_back", "Back to Main Menu"),
        ("q", "quit_app", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Container():
            yield WowFactorHeader(id="app-header")
            yield Static(colorize_text_gradient("ANALYTICS DASHBOARD", RETRO_GRADIENT_COLORS), classes="title compact-header")
            
            with TabbedContent(classes="analytics-container"):
                with TabPane("Average by CPU"):
                    yield PlotextPlot(id="cpu_avg_plot")
                with TabPane("Score Distribution"):
                    yield PlotextPlot(id="score_dist_plot")
                with TabPane("Correlations"):
                    yield Static("Threads vs Score", classes="section-title")
                    yield PlotextPlot(id="threads_scatter_plot")
                    yield Static("Frequency (GHz) vs Score", classes="section-title")
                    yield PlotextPlot(id="freq_scatter_plot")
                with TabPane("Summary & Trends"):
                    # Statistics cards for each CPU model
                    with Container(classes="stats-cards-container"):
                        yield Static("CPU Model Statistics", classes="section-title")
                        yield Static("", id="cpu_stats_cards")
                    
                    # Trend visualization section
                    with Container(classes="trends-container"):
                        yield Static("Performance Trends", classes="section-title")
                        yield Static("", id="trend_sparklines")
            
            with Horizontal(classes="action-buttons compact-button"):
                yield Button("Back", id="back_to_main_menu", variant="default", classes="action-btn")
                yield Button("Generate Report", id="generate_report", variant="primary", classes="action-btn")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#app-header", WowFactorHeader).update_title("ANALYTICS")
        self.load_data()

    def load_data(self) -> None:
        self.run_worker(lambda: self._load_data_worker(), thread=True, group="data_loading")

    def _load_data_worker(self):
        try:
            all_scores = _get_all_valid_scores()
            self.post_message(DataLoadComplete(all_scores))
        except Exception as e:
            logging.error(f"Error loading analytics data: {e}")
            self.post_message(DataLoadError())

    def on_data_load_complete(self, message: DataLoadComplete) -> None:
        self.all_scores = message.data
        self.render_charts()

    def on_data_load_error(self, message: DataLoadError) -> None:
         self.navigation.notify("Error loading analytics data. Please try again.", type="error")

    def on_tabbed_content_tab_changed(self, event: TabbedContent.TabChanged) -> None:
        """Handle tab change to render appropriate plots."""
        selected_tab = event.tab.id if hasattr(event.tab, 'id') else str(event.tab)
        
        # Render scatter plots when Correlations tab is selected
        if "Correlations" in str(event.tab.label):
            self._render_scatter_plots()
        elif "Summary & Trends" in str(event.tab.label):
            self._render_summary_and_trends()

    def render_charts(self) -> None:
        # CPU Average Plot
        cpu_plot = self.query_one("#cpu_avg_plot", PlotextPlot)
        cpu_plot.plt.clear_data()
        
        if hasattr(self, 'all_scores') and self.all_scores:
            cpu_models, avg_scores = aggregate_scores_by_cpu(self.all_scores)
            if cpu_models:
                cpu_plot.plt.bar(cpu_models, avg_scores)
                cpu_plot.plt.title("Average Score by CPU")
                cpu_plot.plt.xlabel("CPU Model")
                cpu_plot.plt.ylabel("Score")
            else:
                cpu_plot.plt.title("No Data Available")
        else:
             cpu_plot.plt.title("No Data Available")

        # Score Distribution Plot
        dist_plot = self.query_one("#score_dist_plot", PlotextPlot)
        dist_plot.plt.clear_data()
        
        if hasattr(self, 'all_scores') and self.all_scores:
            bins, counts = get_score_distribution(self.all_scores)
            if bins:
                dist_plot.plt.bar(bins, counts)
                dist_plot.plt.title("Score Distribution")
                dist_plot.plt.xlabel("Score Range")
                dist_plot.plt.ylabel("Count")
            else:
                dist_plot.plt.title("No Data Available")
        else:
            dist_plot.plt.title("No Data Available")
            
        # Refresh widgets
        cpu_plot.refresh()
        dist_plot.refresh()

    def _render_scatter_plots(self) -> None:
        """Render scatter plots for correlation analysis."""
        if not hasattr(self, 'all_scores') or not self.all_scores:
            threads_plot = self.query_one("#threads_scatter_plot", PlotextPlot)
            freq_plot = self.query_one("#freq_scatter_plot", PlotextPlot)
            threads_plot.plt.title("No Data Available")
            freq_plot.plt.title("No Data Available")
            threads_plot.refresh()
            freq_plot.refresh()
            return
        
        # Set all_scores for AnalyticsEngine methods that need it
        # Set all_scores for AnalyticsEngine methods that need it
        # Extract (threads, score) pairs for Threads vs Score plot
        threads_data = []
        scores_for_threads = []
        
        # Extract (frequency in GHz, score) pairs for Frequency vs Score plot
        freq_data = []
        scores_for_freq = []
        
        for score_data in self.all_scores:
            ops_per_sec = score_data.get('ops_per_second', 0)
            num_threads = score_data.get('num_threads', 1)
            
            # Get frequency from system info, convert to GHz if needed
            sys_info = score_data.get('system', {})
            freq_str = sys_info.get('processor_frequency', 'N/A')
            
            try:
                # Parse frequency - could be "3.5GHz" or similar format
                import re
                freq_match = re.search(r'([\d.]+)\s*GHz', str(freq_str), re.IGNORECASE)
                if freq_match:
                    freq_ghz = float(freq_match.group(1))
                else:
                    # Try parsing as Hz and convert to GHz
                    freq_val = float(str(freq_str).replace('GHz', '').replace('MHz', ''))
                    freq_ghz = freq_val / 1000 if 'MHz' in str(freq_str) else freq_val
                
                freq_data.append(freq_ghz)
                scores_for_freq.append(ops_per_sec)
            except (ValueError, TypeError):
                pass
            
            threads_data.append(num_threads)
            scores_for_threads.append(ops_per_sec)

        # Render Threads vs Score scatter plot
        threads_plot = self.query_one("#threads_scatter_plot", PlotextPlot)
        threads_plot.plt.clear_data()
        
        if threads_data and scores_for_threads:
            threads_plot.plt.scatter(threads_data, scores_for_threads, label="Benchmark Runs")
            
            # Add trend line using simple linear regression
            if len(threads_data) >= 2:
                try:
                    n = len(threads_data)
                    sum_x = sum(threads_data)
                    sum_y = sum(scores_for_threads)
                    sum_xy = sum(x * y for x, y in zip(threads_data, scores_for_threads))
                    sum_xx = sum(x * x for x in threads_data)
                    
                    # Calculate slope and intercept
                    denom = n * sum_xx - sum_x * sum_x
                    if denom != 0:
                        slope = (n * sum_xy - sum_x * sum_y) / denom
                        intercept = (sum_y - slope * sum_x) / n
                        
                        # Generate trend line points
                        min_threads = min(threads_data)
                        max_threads = max(threads_data)
                        trend_x = [min_threads, max_threads]
                        trend_y = [slope * x + intercept for x in trend_x]
                        
                        threads_plot.plt.scatter(trend_x, trend_y, label="Trend", color="red")
                except Exception:
                    pass
            
            threads_plot.plt.title("Threads vs Score (Ops/Second)")
            threads_plot.plt.xlabel("Number of Threads")
            threads_plot.plt.ylabel("Score (Ops/Second)")
            threads_plot.plt.legend()
        else:
            threads_plot.plt.title("No Thread Data Available")

        # Render Frequency vs Score scatter plot
        freq_plot = self.query_one("#freq_scatter_plot", PlotextPlot)
        freq_plot.plt.clear_data()
        
        if freq_data and scores_for_freq:
            freq_plot.plt.scatter(freq_data, scores_for_freq, label="Benchmark Runs")
            
            # Add trend line using simple linear regression
            if len(freq_data) >= 2:
                try:
                    n = len(freq_data)
                    sum_x = sum(freq_data)
                    sum_y = sum(scores_for_freq)
                    sum_xy = sum(x * y for x, y in zip(freq_data, scores_for_freq))
                    sum_xx = sum(x * x for x in freq_data)
                    
                    # Calculate slope and intercept
                    denom = n * sum_xx - sum_x * sum_x
                    if denom != 0:
                        slope = (n * sum_xy - sum_x * sum_y) / denom
                        intercept = (sum_y - slope * sum_x) / n
                        
                        # Generate trend line points
                        min_freq = min(freq_data)
                        max_freq = max(freq_data)
                        trend_x = [min_freq, max_freq]
                        trend_y = [slope * x + intercept for x in trend_x]
                        
                        freq_plot.plt.scatter(trend_x, trend_y, label="Trend", color="red")
                except Exception:
                    pass
            
            freq_plot.plt.title("Frequency (GHz) vs Score (Ops/Second)")
            freq_plot.plt.xlabel("Frequency (GHz)")
            freq_plot.plt.ylabel("Score (Ops/Second)")
            freq_plot.plt.legend()
        else:
            freq_plot.plt.title("No Frequency Data Available")

        # Refresh widgets
        threads_plot.refresh()
        freq_plot.refresh()

    def _render_summary_and_trends(self) -> None:
        """
        Render the Summary & Trends tab with statistics cards and sparklines.
        Uses the AnalyticsEngine for calculations.
        """
        if not hasattr(self, 'all_scores') or not self.all_scores:
            # No data available
            stats_container = self.query_one("#cpu_stats_cards", Static)
            trends_container = self.query_one("#trend_sparklines", Static)
            stats_container.update("No benchmark data available")
            trends_container.update("No trend data available")
            return
        
        # Initialize AnalyticsEngine with the loaded scores
        engine = AnalyticsEngine()
        engine._scores_cache = self.all_scores
        
        # Get statistics per CPU model
        cpu_stats = engine.get_stats_per_cpu_model()
        
        # Build statistics cards display
        stats_lines = []
        for cpu_model, stats in cpu_stats.items():
            ops_stats = stats['ops_per_second']
            duration_stats = stats['duration_seconds']
            
            card = f"\n┌─ {cpu_model[:40]} ────────────────────────┐"
            card += f"\n│ Samples: {stats['sample_count']}                    │"
            card += f"\n│ Ops/Sec - Mean: {ops_stats['mean']:>12,.1f} │"
            card += f"\n│           Median: {ops_stats['median']:>10,.1f}  │"
            card += f"\n│           Std Dev: {ops_stats['std_dev']:>9,.1f}   │"
            card += f"\n│           Min/Max: {ops_stats['min']:>8,.0f}/{ops_stats['max']:>8,.0f}  │"
            card += f"\n│ Duration - Mean: {duration_stats['mean']:>12,.2f}s │"
            card += f"\n└───────────────────────────────────────────────┘"
            stats_lines.append(card)
        
        if not stats_lines:
            stats_lines.append("No CPU models found")
        
        stats_container = self.query_one("#cpu_stats_cards", Static)
        stats_container.update('\n'.join(stats_lines))
        
        # Build trend sparklines
        by_cpu_model = engine.get_scores_by_cpu_model()
        trend_lines = []
        for cpu_model, scores in by_cpu_model.items():
            if len(scores) < 2:
                continue
            
            trend_info = engine.detect_trends(scores)
            sparkline = engine.get_trend_visualization(scores)
            
            # Add color indicator based on trend direction
            trend_indicator = "↑" if trend_info['trend'] == 'improving' else ("↓" if trend_info['trend'] == 'degrading' else "→")
            
            line = f"\n{cpu_model}:"
            line += f"\n  {sparkline}"
            line += f"\n  Trend: [{trend_indicator}] {trend_info['trend'].upper()} ({trend_info['change_rate']:+.1f}% change)"
            trend_lines.append(line)
        
        if not trend_lines:
            trend_lines.append("Insufficient data for trend analysis")
        
        trends_container = self.query_one("#trend_sparklines", Static)
        trends_container.update('\n'.join(trend_lines))
    
    def _generate_analytics_report(self) -> None:
        """
        Generate and export an analytics summary report.
        Uses the AnalyticsEngine to compile comprehensive data.
        """
        if not hasattr(self, 'all_scores') or not self.all_scores:
            self.navigation.notify("No benchmark data available for reporting", type="error")
            return
        
        # Initialize AnalyticsEngine and generate report
        engine = AnalyticsEngine()
        summary_report = engine.generate_summary_report()
        
        if 'error' in summary_report:
            self.navigation.notify(f"Error generating report: {summary_report['error']}", type="error")
            return
        
        # Export to JSON format
        import json
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analytics_report_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(summary_report, f, indent=2)
            self.navigation.notify(f"Analytics report saved to {filename}", type="success")
        except IOError as e:
            self.navigation.notify(f"Error saving report: {e}", type="error")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back_to_main_menu":
            self.action_go_back()
            event.stop()
        elif event.button.id == "generate_report":
            self._generate_analytics_report()
            event.stop()
        elif event.button.id == "quit_app":
            self.app.exit()
            event.stop()
