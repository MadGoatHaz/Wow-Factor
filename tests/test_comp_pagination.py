#!/usr/bin/env python3
"""
Pagination tests from the comprehensive test suite.
Tests page calculations, navigation, and boundary conditions.
"""

import os
import sys
import json
import tempfile
import shutil
import unittest
from unittest.mock import Mock

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.benchmark import (
    _get_all_valid_scores, _invalidate_all_cache, _cache
)
from ui.screens.views import ViewAllScoresScreen


class TestPaginationComprehensive(unittest.TestCase):
    """Test pagination functionality from comprehensive suite"""

    def setUp(self):
        """Set up test environment"""
        self.test_data_dir = tempfile.mkdtemp(prefix="wow_test_")
        self.original_dir = os.getcwd()
        os.chdir(self.test_data_dir)

        # Force clear cache
        try:
            from core import benchmark as wow_core
            if hasattr(wow_core, '_cache'):
                wow_core._cache.clear()
            from core.benchmark import _invalidate_all_cache, _cache
            _invalidate_all_cache()
            _cache.clear()
            if 'core.benchmark' in sys.modules:
                sys.modules['core.benchmark']._cache.clear()
        except Exception:
            pass

        # Create benchmark results directory
        os.makedirs("benchmark_results", exist_ok=True)

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_data_dir, ignore_errors=True)

    def _create_large_dataset(self, count=150):
        """Create a large dataset for pagination testing"""
        for i in range(count):
            data = {
                "timestamp": f"2025-11-{20 + (i % 10):02d} 10:00:00",
                "duration_seconds": 15.0,
                "total_operations": 1000000 + i * 1000,
                "ops_per_second": 100000.0 + i * 100,
                "num_threads": 4,
                "system": {
                    "platform": "Linux" if i % 2 == 0 else "Windows",
                    "processor_model": f"Test CPU Model {i % 5}",
                    "processor_frequency": "3.5GHz"
                }
            }
            filename = f"benchmark_results/test_{i:03d}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)

    def test_pagination_calculation(self):
        """Test pagination calculations"""
        screen = ViewAllScoresScreen()

        # Test with empty dataset
        screen.total_items = 0
        screen.page_size = 50
        screen._calculate_pages()
        self.assertEqual(screen.total_pages, 1)

        # Test with small dataset
        screen.total_items = 25
        screen._calculate_pages()
        self.assertEqual(screen.total_pages, 1)

        # Test with large dataset
        screen.total_items = 150
        screen._calculate_pages()
        self.assertEqual(screen.total_pages, 3)  # 150 / 50 = 3 pages

        # Test with exact page boundary
        screen.total_items = 100
        screen._calculate_pages()
        self.assertEqual(screen.total_pages, 2)  # 100 / 50 = 2 pages

    def test_page_navigation(self):
        """Test page navigation functionality"""
        self._create_large_dataset(150)

        screen = ViewAllScoresScreen()
        # Mock query_one to avoid mounting issues
        mock_table = Mock()
        mock_table.columns = {}
        mock_table.rows = []
        mock_table.clear = Mock()
        mock_table.add_column = Mock()
        mock_table.add_row = Mock()

        mock_input = Mock()
        mock_input.value = "1"

        def query_one_side_effect(selector, type=None):
            if "table" in selector or selector == "#all_scores_table":
                return mock_table
            if "input" in selector or selector == "#page_input":
                return mock_input
            return Mock()

        screen.query_one = Mock(side_effect=query_one_side_effect)

        scores = _get_all_valid_scores()
        screen.original_all_scores = scores
        screen.filtered_scores = scores
        screen.total_items = len(scores)
        screen.page_size = 50
        screen._calculate_pages()

        # Test initial page
        self.assertEqual(screen.current_page, 1)

        # Test next page
        screen._go_to_next_page()
        self.assertEqual(screen.current_page, 2)

        # Test previous page
        screen._go_to_previous_page()
        self.assertEqual(screen.current_page, 1)

        # Test last page
        screen._go_to_last_page()
        self.assertEqual(screen.current_page, 3)

        # Test first page
        screen._go_to_first_page()
        self.assertEqual(screen.current_page, 1)

    def test_page_boundaries(self):
        """Test navigation at page boundaries"""
        self._create_large_dataset(150)

        screen = ViewAllScoresScreen()
        scores = _get_all_valid_scores()
        screen.original_all_scores = scores
        screen.filtered_scores = scores
        screen.total_items = len(scores)
        screen.page_size = 50
        screen._calculate_pages()

        # Test navigation beyond first page
        screen.current_page = 1
        screen._go_to_previous_page()  # Should stay at page 1
        self.assertEqual(screen.current_page, 1)

        # Test navigation beyond last page
        screen.current_page = 3
        screen._go_to_next_page()  # Should stay at page 3
        self.assertEqual(screen.current_page, 3)


if __name__ == "__main__":
    unittest.main()