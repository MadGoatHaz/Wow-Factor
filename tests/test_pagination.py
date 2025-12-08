"""
Test script for pagination functionality in ViewAllScoresScreen.
This test verifies that the pagination logic works correctly.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.components import ViewAllScoresScreen
from textual.widgets import DataTable


def test_pagination_initialization():
    """Test that pagination is initialized correctly."""
    print("Testing pagination initialization...")
    
    # Create a mock screen instance
    screen = ViewAllScoresScreen()
    
    # Check that pagination attributes are set
    assert hasattr(screen, 'current_page')
    assert hasattr(screen, 'page_size')
    assert hasattr(screen, 'total_pages')
    assert hasattr(screen, 'total_items')
    
    print("✓ Pagination attributes initialized correctly")


def test_pagination_calculation():
    """Test pagination calculation with different item counts."""
    print("Testing pagination calculation...")
    
    # Test with 0 items
    screen = ViewAllScoresScreen()
    # Set page size to 20 for these tests
    screen.page_size = 20
    screen.total_items = 0
    screen._calculate_pages()
    assert screen.total_pages == 1
    assert screen.current_page == 1
    
    # Test with exactly one page
    screen.total_items = 20
    screen._calculate_pages()
    assert screen.total_pages == 1
    assert screen.current_page == 1
    
    # Test with multiple pages
    screen.total_items = 45  # 3 pages (20, 20, 5)
    screen._calculate_pages()
    assert screen.total_pages == 3
    assert screen.current_page == 1
    
    print("✓ Pagination calculation works correctly")


def test_pagination_navigation():
    """Test pagination navigation logic."""
    print("Testing pagination navigation...")
    
    screen = ViewAllScoresScreen()
    screen.page_size = 20
    screen.total_items = 45  # 3 pages
    screen._calculate_pages()

    # Mock _display_current_page and _update_pagination_display since they touch UI widgets
    screen._display_current_page = lambda: None
    screen._update_pagination_display = lambda: None
    
    # Mock query_one for page_input
    class MockInput:
        value = "1"
    
    class MockQueryOne:
        def __init__(self):
            self.input = MockInput()
        def __call__(self, selector, type=None):
            return self.input
            
    screen.query_one = MockQueryOne()
    
    # Test next page
    screen._go_to_next_page()
    assert screen.current_page == 2
    
    # Test previous page
    screen._go_to_previous_page()
    assert screen.current_page == 1
    
    # Test going to last page
    screen._go_to_last_page()
    assert screen.current_page == 3
    
    # Test going to first page
    screen._go_to_first_page()
    assert screen.current_page == 1
    
    print("✓ Pagination navigation works correctly")


if __name__ == "__main__":
    print("Running pagination tests...")
    try:
        test_pagination_initialization()
        test_pagination_calculation()
        test_pagination_navigation()
        print("\n✅ All pagination tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise