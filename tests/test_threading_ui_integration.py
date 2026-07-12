import unittest
from unittest.mock import MagicMock, patch
import threading
from ui.screens.benchmark import RunSingleBenchmarkScreen
from ui.messages import BenchmarkCompletion

class TestThreadingUIIntegration(unittest.TestCase):
    def setUp(self):
        # Create instance of the screen
        self.screen = RunSingleBenchmarkScreen()
        
        # Mock Textual-specific attributes/methods that we can't easily instantiate in a unit test
        self.screen.post_message = MagicMock()
        self.screen.query_one = MagicMock()
        self.screen.run_worker = MagicMock()
        # self.screen.app cannot be set directly as it is a property
        # We can bypass this by mocking the property on the class or just relying on internal handling if possible,
        # but since we might access self.screen.app, let's patch the property on the instance if possible,
        # or simply mock the _app attribute which Textual likely uses or just ignore it if not used in tested methods.
        # But wait, looking at the code, app is used in `action_go_back` (self.app.pop_screen) and `quit` (self.app.exit).
        # It is NOT used in start_benchmark_run's validation logic or on_benchmark_completion.
        # So we can likely skip setting it. If it IS used, we'd need to mock the property return value.
        
        # To be safe in case future logic uses it:
        type(self.screen).app = MagicMock()
        # Populate SCREENS registry for NavigationManager.navigate_to calls
        self.screen.app.SCREENS = {"loading_overlay": MagicMock()}

        # Create mock widgets ensuring they have the attributes accessed by the screen code
        self.mock_duration_input = MagicMock()
        self.mock_duration_input.value = "10"
        
        self.mock_threads_input = MagicMock()
        self.mock_threads_input.value = "4"
        
        self.mock_progress_display = MagicMock()
        self.mock_start_btn = MagicMock()
        self.mock_stop_btn = MagicMock()
        self.mock_back_btn = MagicMock()
        self.mock_summary_display = MagicMock()
        self.mock_markdown_display = MagicMock()
        
        # Configure query_one to return specific mocks based on ID
        def side_effect(selector, type_hint=None):
            if "#duration_input" in selector: return self.mock_duration_input
            if "#threads_input" in selector: return self.mock_threads_input
            if "#progress_display" in selector: return self.mock_progress_display
            if "#start_benchmark" in selector: return self.mock_start_btn
            if "#stop_benchmark" in selector: return self.mock_stop_btn
            if "#back_to_main_menu" in selector: return self.mock_back_btn
            if "#result_summary_display" in selector: return self.mock_summary_display
            if "#result_markdown_display" in selector: return self.mock_markdown_display
            return MagicMock()

        self.screen.query_one.side_effect = side_effect
        
        # Mock NavigationManager.notify to avoid ToastNotification UI setup
        # and capture calls for assertion
        self.screen._navigation = None  # Reset so navigation property creates fresh instance
        nav = self.screen.navigation
        nav.notify = MagicMock()
        nav.navigate_to = MagicMock()
        nav.go_back = MagicMock()

    def test_start_benchmark_validation_valid(self):
        """Test that start_benchmark_run processes valid inputs correctly."""
        self.screen.start_benchmark_run()
        
        # Verify UI state changes
        self.assertTrue(self.mock_start_btn.disabled)
        self.assertFalse(self.mock_stop_btn.disabled)
        self.assertTrue(self.mock_stop_btn.display)
        
        # Verify worker was started
        self.screen.run_worker.assert_called_once()
        
        # Verify correct args were parsed (duration=10, infinite=False, threads=4)
        # Note: We can't easily inspect the coroutine passed to run_worker without complexity,
        # but the fact it was called implies validation passed.

    def test_start_benchmark_validation_invalid_threads(self):
        """Test that start_benchmark_run handles invalid thread counts."""
        self.mock_threads_input.value = "0" # Invalid
        
        self.screen.start_benchmark_run()
        
        # Verify error notification via navigation service
        self.screen.navigation.notify.assert_called_with(
            "Thread count must be at least 1.", type="error"
        )
        
        # Verify worker was NOT started
        self.screen.run_worker.assert_not_called()

    def test_start_benchmark_validation_non_integer_threads(self):
        """Test that start_benchmark_run handles non-integer thread inputs."""
        self.mock_threads_input.value = "four" # Invalid
        
        self.screen.start_benchmark_run()
        
        # Verify error notification via navigation service
        self.screen.navigation.notify.assert_called_with(
            "Invalid thread count. Please enter a positive integer.", type="error"
        )
        
        # Verify worker was NOT started
        self.screen.run_worker.assert_not_called()
        
    def test_start_benchmark_validation_max_threads_warning(self):
        """
        Ideally we would test max threads warning if implemented, 
        but currently the code just checks >= 1.
        Just verifying standard behavior for a high but valid number.
        """
        self.mock_threads_input.value = "128"
        self.screen.start_benchmark_run()
        self.screen.run_worker.assert_called_once()

    def test_on_benchmark_completion_success(self):
        """Test the UI update on successful benchmark completion."""
        # Create a mock completion message
        result_data = {
            "total_operations": 1000,
            "ops_per_second": 100.0,
            "duration_seconds": 10.0,
            "num_threads": 4,
            "system": {
                "processor_model": "Test CPU",
                "processor_frequency": "3.0GHz",
                "platform": "Linux"
            },
            "file_path": "/tmp/test.json"
        }
        message = BenchmarkCompletion(result_data)
        
        self.screen.on_benchmark_completion(message)
        
        # Verify notification sent via navigation service
        self.screen.navigation.notify.assert_any_call(
            "Benchmark completed successfully!", type="success"
        )
        # Verify UI state changes
        self.assertFalse(self.mock_start_btn.disabled)
        self.assertTrue(self.mock_stop_btn.disabled)
        self.assertFalse(self.mock_stop_btn.display)
        
        # Verify summary display update containing key info
        args, _ = self.mock_summary_display.update.call_args
        summary_text = args[0]
        self.assertIn("Total Operations", summary_text)
        # format_large_number(1000) returns "1.00K"
        self.assertIn("1.00K", summary_text)
        self.assertIn("Threads: [green]4[/green]", summary_text)

if __name__ == "__main__":
    unittest.main()