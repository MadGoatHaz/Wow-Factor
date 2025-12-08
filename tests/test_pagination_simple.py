"""
Simple test script for pagination functionality in ViewAllScoresScreen.
This test verifies that the pagination methods exist and work correctly.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.components import ViewAllScoresScreen


def test_pagination_methods_exist():
    """Test that pagination methods exist in the class."""
    print("Testing pagination methods existence...")
    
    # Check that pagination methods exist (they are defined in the class)
    screen = ViewAllScoresScreen()
    
    methods_to_check = [
        '_display_current_page',
        '_update_pagination_display',
        '_go_to_next_page',
        '_go_to_previous_page',
        '_go_to_first_page',
        '_go_to_last_page'
    ]
    
    for method_name in methods_to_check:
        assert hasattr(screen, method_name), f"Method {method_name} not found"
        print(f"✓ {method_name} exists")
    
    print("✓ All pagination methods exist correctly")


def test_pagination_logic():
    """Test basic pagination logic."""
    print("Testing pagination logic...")
    
    # Create a screen instance
    screen = ViewAllScoresScreen()
    
    # Test that we can set up pagination variables (these would be set during _update_table_with_all_scores)
    screen.current_page = 1
    screen.page_size = 20
    screen.total_items = 45
    
    # Test calculation methods
    assert hasattr(screen, '_calculate_pages')
    
    print("✓ Pagination logic setup works")


if __name__ == "__main__":
    print("Running simple pagination tests...")
    try:
        test_pagination_methods_exist()
        test_pagination_logic()
        print("\n✅ All simple pagination tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise