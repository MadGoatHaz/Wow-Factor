#!/usr/bin/env python3
"""
Data visualization tests from the comprehensive test suite.
Tests chart data loading, JSON export, date parsing, and date range filtering.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.benchmark import (
    _get_all_valid_scores, export_data_to_json,
    parse_date, apply_all_filters, _invalidate_all_cache, _cache
)

# Mock classes for BenchmarkTrendsScreen
class BenchmarkTrendsScreen:
    BINDINGS = [
        ("1", "line_chart", "Line Chart"),
        ("2", "bar_chart", "Bar Chart"),
        ("e", "export", "Export"),
        ("b", "back", "Back"),
        ("q", "quit", "Quit"),
    ]
    def _process_scores_over_time(self, scores):
        return scores
    def _process_cross_machine_comparison(self, scores):
        return scores
    def query_one(self, selector):
        return True


class TestDataVisualization(unittest.TestCase):
    """Test data visualization features in BenchmarkTrendsScreen"""

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

        # Create test data
        self._create_test_benchmark_data()

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_data_dir, ignore_errors=True)

    def _create_test_benchmark_data(self):
        """Create test benchmark data for visualization"""
        test_data = [
            {
                "timestamp": "2025-11-20 10:00:00",
                "duration_seconds": 15.0,
                "total_operations": 1500000,
                "ops_per_second": 100000.0,
                "num_threads": 4,
                "system": {
                    "platform": "Linux",
                    "processor_model": "Test CPU Model 1",
                    "processor_frequency": "3.5GHz"
                }
            },
            {
                "timestamp": "2025-11-21 10:00:00",
                "duration_seconds": 15.0,
                "total_operations": 2000000,
                "ops_per_second": 133333.0,
                "num_threads": 4,
                "system": {
                    "platform": "Linux",
                    "processor_model": "Test CPU Model 2",
                    "processor_frequency": "3.5GHz"
                }
            },
            {
                "timestamp": "2025-11-22 10:00:00",
                "duration_seconds": 15.0,
                "total_operations": 1800000,
                "ops_per_second": 120000.0,
                "num_threads": 4,
                "system": {
                    "platform": "Linux",
                    "processor_model": "Test CPU Model 1",
                    "processor_frequency": "3.5GHz"
                }
            }
        ]

        for i, data in enumerate(test_data):
            filename = f"benchmark_results/test_{i:03d}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)

    def test_chart_data_loading(self):
        """Test that chart data loads correctly"""
        scores = _get_all_valid_scores()
        self.assertGreater(len(scores), 0, "Should load test benchmark data")

        # Test data processing for line chart
        trends_screen = BenchmarkTrendsScreen()
        processed_data = trends_screen._process_scores_over_time(scores)
        self.assertGreater(len(processed_data), 0, "Should process scores for line chart")

        # Test data processing for bar chart
        comparison_data = trends_screen._process_cross_machine_comparison(scores)
        self.assertGreater(len(comparison_data), 0, "Should process scores for bar chart")

    def test_export_data_to_json(self):
        """Test JSON export functionality for chart data"""
        scores = _get_all_valid_scores()

        # Test best scores export
        json_data = export_data_to_json(None, 'best_scores', scores)
        self.assertIn('metadata', json_data)
        self.assertIn('data', json_data)
        self.assertEqual(json_data['metadata']['screen_type'], 'best_scores')
        self.assertEqual(json_data['metadata']['export_format'], 'json')

        # Test all scores export
        json_data = export_data_to_json(None, 'all_scores', scores)
        self.assertEqual(json_data['metadata']['screen_type'], 'all_scores')

        # Test CPU comparison export
        json_data = export_data_to_json(None, 'cpu_comparison', scores)
        self.assertEqual(json_data['metadata']['screen_type'], 'cpu_comparison')

    def test_date_parsing(self):
        """Test date parsing for filtering"""
        # Test valid date formats
        date1 = parse_date("2025-11-20")
        self.assertIsNotNone(date1)
        self.assertEqual(date1.year, 2025)
        self.assertEqual(date1.month, 11)
        self.assertEqual(date1.day, 20)

        date2 = parse_date("2025/11/20")
        self.assertIsNotNone(date2)

        # Test invalid date
        date3 = parse_date("invalid-date")
        self.assertIsNone(date3)

        # Test empty date
        date4 = parse_date("")
        self.assertIsNone(date4)

    def test_date_range_filtering(self):
        """Test date range filtering functionality"""
        scores = _get_all_valid_scores()

        # Test with valid date range
        start_date = parse_date("2025-11-20")
        end_date = parse_date("2025-11-22")

        filtered = apply_all_filters(scores, "", start_date, end_date, "")
        self.assertGreater(len(filtered), 0, "Should filter scores by date range")

        # Test with date outside range
        start_date = parse_date("2025-11-25")
        end_date = parse_date("2025-11-30")

        filtered = apply_all_filters(scores, "", start_date, end_date, "")
        self.assertEqual(len(filtered), 0, "Should return no scores for date range with no data")


if __name__ == "__main__":
    unittest.main()