#!/usr/bin/env python3
"""
Search and filter tests from the comprehensive test suite.
Tests text search, platform filtering, combined filters, and unique platforms.
"""

import os
import sys
import json
import tempfile
import shutil
import unittest

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.benchmark import (
    _get_all_valid_scores, parse_date, apply_all_filters,
    get_unique_platforms, _invalidate_all_cache, _cache
)


class TestSearchFiltersComprehensive(unittest.TestCase):
    """Test search and filter functionality from comprehensive suite"""

    def setUp(self):
        """Set up test environment"""
        self.test_data_dir = tempfile.mkdtemp(prefix="wow_test_")
        self.original_dir = os.getcwd()
        os.chdir(self.test_data_dir)

        # Invalidate cache
        try:
            from core import benchmark as wow_core
            if hasattr(wow_core, '_cache'):
                wow_core._cache.clear()
            _invalidate_all_cache()
            _cache.clear()
        except Exception:
            pass

        # Create benchmark results directory
        os.makedirs("benchmark_results", exist_ok=True)

        # Create diverse test data
        self._create_diverse_test_data()

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_data_dir, ignore_errors=True)

    def _create_diverse_test_data(self):
        """Create diverse test data for filtering"""
        platforms = ["Linux", "Windows", "Darwin"]
        cpu_models = ["Intel i7-9700K", "AMD Ryzen 7 3700X", "Intel i9-10900K", "AMD Ryzen 9 5900X"]

        for i in range(30):
            data = {
                "timestamp": f"2025-11-{10 + (i % 20):02d} 10:00:00",
                "duration_seconds": 15.0,
                "total_operations": 1000000 + i * 50000,
                "ops_per_second": 100000.0 + i * 5000,
                "num_threads": 4 + (i % 4),
                "system": {
                    "platform": platforms[i % len(platforms)],
                    "processor_model": cpu_models[i % len(cpu_models)],
                    "processor_frequency": "3.5GHz"
                }
            }
            filename = f"benchmark_results/test_{i:03d}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)

    def test_search_functionality(self):
        """Test text search across different fields"""
        scores = _get_all_valid_scores()
        self.assertGreater(len(scores), 0, "Should load test data")

        # Test CPU model search
        filtered = apply_all_filters(scores, "Intel", None, None, "")
        self.assertGreater(len(filtered), 0, "Should find Intel CPUs")
        for score in filtered:
            self.assertIn("Intel", score['system']['processor_model'])

        # Test platform search
        filtered = apply_all_filters(scores, "Linux", None, None, "")
        self.assertGreater(len(filtered), 0, "Should find Linux platforms")
        for score in filtered:
            self.assertEqual(score['system']['platform'], "Linux")

        # Test ops/second search
        filtered = apply_all_filters(scores, "120000", None, None, "")
        self.assertGreater(len(filtered), 0, "Should find scores with 120000")

    def test_platform_filter(self):
        """Test platform filtering"""
        scores = _get_all_valid_scores()

        # Test exact platform match
        filtered = apply_all_filters(scores, "", None, None, "Linux")
        self.assertGreater(len(filtered), 0, "Should find Linux platforms")
        for score in filtered:
            self.assertEqual(score['system']['platform'], "Linux")

        # Test non-existent platform
        filtered = apply_all_filters(scores, "", None, None, "NonExistent")
        self.assertEqual(len(filtered), 0, "Should find no platforms for non-existent platform")

        # Test case sensitivity
        filtered = apply_all_filters(scores, "", None, None, "linux")
        self.assertEqual(len(filtered), 0, "Platform filter should be case-sensitive")

    def test_combined_filters(self):
        """Test combination of multiple filters"""
        scores = _get_all_valid_scores()

        # Test search + platform filter
        start_date = parse_date("2025-11-10")
        end_date = parse_date("2025-11-15")
        filtered = apply_all_filters(scores, "Intel", start_date, end_date, "Linux")

        self.assertGreater(len(filtered), 0, "Should find scores with combined filters")
        for score in filtered:
            self.assertIn("Intel", score['system']['processor_model'])
            self.assertEqual(score['system']['platform'], "Linux")
            # Check date range
            score_date = parse_date(score['timestamp'].split()[0])
            self.assertGreaterEqual(score_date, start_date)
            self.assertLessEqual(score_date, end_date)

    def test_unique_platforms_extraction(self):
        """Test extraction of unique platforms from data"""
        scores = _get_all_valid_scores()
        platforms = get_unique_platforms(scores)

        self.assertGreater(len(platforms), 0, "Should extract platforms")
        self.assertIn("Linux", platforms)
        self.assertIn("Windows", platforms)
        self.assertIn("Darwin", platforms)


if __name__ == "__main__":
    unittest.main()