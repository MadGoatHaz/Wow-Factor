import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add current directory to path to allow importing local modules
sys.path.append(os.getcwd())

# Attempt to mock textual_plotext if it's not installed, 
# to ensure the test can run in environments where dependencies might be missing
# but we still want to test the logic flow.
try:
    import textual_plotext
except ImportError:
    mock_plotext = MagicMock()
    sys.modules["textual_plotext"] = mock_plotext
    # We also need to mock the PlotextPlot class specifically if it's imported directly
    mock_plotext.PlotextPlot = MagicMock

# Now import the component to test
from ui.screens.analytics import AnalyticsScreen

class TestChartsUI(unittest.TestCase):
    def test_render_charts_flow(self):
        """
        Verify that AnalyticsScreen.render_charts passes correct data to PlotextPlot.
        """
        print("\n--- Testing AnalyticsScreen Chart Rendering Flow ---")
        
        # 1. Instantiate AnalyticsScreen
        screen = AnalyticsScreen()
        print("1. Instantiated AnalyticsScreen")
        
        # 2. Mock the query_one method to return mock plots
        # We need two distinct mocks for the two plots to verify them independently
        mock_cpu_plot = MagicMock()
        mock_dist_plot = MagicMock()
        
        # Each plot has a .plt attribute (the plotext wrapper) which receives the plotting commands
        mock_cpu_plt = MagicMock()
        mock_cpu_plot.plt = mock_cpu_plt
        
        mock_dist_plt = MagicMock()
        mock_dist_plot.plt = mock_dist_plt
        
        # Setup query_one side effect to return the correct mock based on the CSS selector
        def query_one_side_effect(selector, type_hint=None):
            if selector == "#cpu_avg_plot":
                return mock_cpu_plot
            elif selector == "#score_dist_plot":
                return mock_dist_plot
            raise ValueError(f"Unexpected selector: {selector}")
            
        screen.query_one = MagicMock(side_effect=query_one_side_effect)
        print("2. Mocked query_one and PlotextPlot widgets")
        
        # 3. Inject sample data into AnalyticsScreen.all_scores
        # The structure is representative of what wow_core produces
        sample_data = [
            {"system": {"processor_model": "CPU A"}, "ops_per_second": 100},
            {"system": {"processor_model": "CPU B"}, "ops_per_second": 200},
        ]
        screen.all_scores = sample_data
        print("3. Injected sample data into screen.all_scores")
        
        # 4. Patch the aggregation functions in ui.screens.analytics to return controlled data
        # This isolates the test from wow_core logic and focuses on the UI data flow
        with patch('ui.screens.analytics.aggregate_scores_by_cpu') as mock_agg, \
             patch('ui.screens.analytics.get_score_distribution') as mock_dist_func:
            
            # Define return values for the helpers to verify they are passed to the plot
            expected_cpus = ["CPU A", "CPU B"]
            expected_scores = [100.0, 200.0]
            mock_agg.return_value = (expected_cpus, expected_scores)
            
            expected_bins = ["0-100", "100-200"]
            expected_counts = [5, 10]
            mock_dist_func.return_value = (expected_bins, expected_counts)
            
            # 5. Call AnalyticsScreen.render_charts()
            print("4. Calling render_charts()...")
            screen.render_charts()
            
            # 6. Assert that plt.bar was called for both charts with correct data
            
            # --- CPU Plot Assertions ---
            print("5. Verifying CPU Plot calls...")
            # Check if clear_data was called
            mock_cpu_plt.clear_data.assert_called_once()
            
            # Check if the correct data was passed to bar()
            # We expect: plt.bar(["CPU A", "CPU B"], [100.0, 200.0])
            mock_cpu_plt.bar.assert_called_with(expected_cpus, expected_scores)
            print("   [PASS] CPU Plot received correct data")
            
            # Check titles/labels
            mock_cpu_plt.title.assert_called_with("Average Score by CPU")
            mock_cpu_plt.xlabel.assert_called_with("CPU Model")
            
            # --- Distribution Plot Assertions ---
            print("6. Verifying Distribution Plot calls...")
            # Check if clear_data was called
            mock_dist_plt.clear_data.assert_called_once()
            
            # Check if the correct data was passed to bar()
            # We expect: plt.bar(["0-100", "100-200"], [5, 10])
            mock_dist_plt.bar.assert_called_with(expected_bins, expected_counts)
            print("   [PASS] Distribution Plot received correct data")
            
            # Check titles/labels
            mock_dist_plt.title.assert_called_with("Score Distribution")
            mock_dist_plt.ylabel.assert_called_with("Count")
            
            # --- Refresh Assertions ---
            mock_cpu_plot.refresh.assert_called_once()
            mock_dist_plot.refresh.assert_called_once()
            print("7. Verified widgets were refreshed")
            
        print("\nSUCCESS: Data flowed correctly from screen to charts.")

if __name__ == "__main__":
    unittest.main()