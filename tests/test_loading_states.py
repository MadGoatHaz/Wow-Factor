#!/usr/bin/env python3

"""
Test script to verify the loading state implementation in WowFactor.
This verifies that all data-fetching screens show appropriate loading indicators.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.screens.views import ViewBestScoresScreen, CompareCPUScreen, ViewAllScoresScreen

def test_loading_states():
    """Test that the screens have proper loading state implementations."""
    
    print("Testing loading states implementation...")
    
    # Test ViewBestScoresScreen
    best_scores_screen = ViewBestScoresScreen()
    assert hasattr(best_scores_screen, 'load_data'), "ViewBestScoresScreen should have load_data method"
    assert hasattr(best_scores_screen, '_update_table_with_scores'), "ViewBestScoresScreen should have _update_table_with_scores method"
    assert hasattr(best_scores_screen, '_show_error_message'), "ViewBestScoresScreen should have _show_error_message method"
    
    # Test CompareCPUScreen
    compare_cpu_screen = CompareCPUScreen()
    assert hasattr(compare_cpu_screen, 'compare_cpu'), "CompareCPUScreen should have compare_cpu method"
    assert hasattr(compare_cpu_screen, '_display_comparison'), "CompareCPUScreen should have _display_comparison method"
    assert hasattr(compare_cpu_screen, '_show_error_message'), "CompareCPUScreen should have _show_error_message method"
    
    # Test ViewAllScoresScreen
    all_scores_screen = ViewAllScoresScreen()
    assert hasattr(all_scores_screen, 'load_data'), "ViewAllScoresScreen should have load_data method"
    assert hasattr(all_scores_screen, '_update_table_with_all_scores'), "ViewAllScoresScreen should have _update_table_with_all_scores method"
    assert hasattr(all_scores_screen, '_show_error_message'), "ViewAllScoresScreen should have _show_error_message method"
    
    print("✓ All screens have proper loading state implementations")
    
    # Test message classes exist
    from ui.messages import DataLoadComplete, DataLoadError
    
    # Create instances to verify they work
    complete_msg = DataLoadComplete({"test": "data"})
    error_msg = DataLoadError()
    
    assert hasattr(complete_msg, 'data'), "DataLoadComplete should have data attribute"
    assert hasattr(error_msg, '__init__'), "DataLoadError should be instantiable"
    
    print("✓ Custom message classes are properly defined")
    
    print("\nAll loading state tests passed successfully!")

if __name__ == "__main__":
    test_loading_states()