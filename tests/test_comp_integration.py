#!/usr/bin/env python3
"""
Integration tests from the comprehensive test suite.
Tests combined filters with pagination and large dataset performance.
"""

import os
import sys
import json
import time
import tempfile
import shutil
import unittest

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.benchmark import (
    _get_all_valid_scores, parse_date, apply_all_filters,
    export_data_to_json, _invalidate_all_cache, _cache
)


class TestIntegrationComprehensive(unittest.TestCase):
    """Test integration of multiple features from comprehensive suite"""

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
            _invalidate_all_cache()
            _cache.clear()
            if 'core.benchmark' in sys.modules:
                sys.modules['core.benchmark']._cache.clear()
        except Exception:
            pass

        # Create benchmark results directory
        os.makedirs("benchmark_results", exist_ok=True)

        # Create test data
        self._create_integration_test_data()

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_data_dir, ignore_errors=True)

    def _create_integration_test_data(self):
        """Create test data for integration testing"""
        for i in range(100):
            data = {
                "timestamp": f"2025-11-{10 + (i % 20):02d} 10:00:00",
                "duration_seconds": 15.0,
                "total_operations": 1000000 + i * 10000,
                "ops_per_second": 100000.0 + i * 1000,
                "num_threads": 4 + (i % 4),
                "system": {
                    "platform": "Linux" if i % 3 == 0 else "Windows",
                    "processor_model": f"Test CPU {i % 10}",
                    "processor_frequency": "3.5GHz"
                }
            }
            filename = f"benchmark_results/test_{i:03d}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)

    def test_filters_with_pagination(self):
        """Test filters combined with pagination"""
        scores = _get_all_valid_scores()

        # Apply filters
        start_date = parse_date("2025-11-15")
        end_date = parse_date("2025-11-25")
        filtered = apply_all_filters(scores, "CPU 1", start_date, end_date, "Linux")

        self.assertGreater(len(filtered), 0, "Should filter data")

        # Simulate pagination
        page_size = 10
        total_pages = (len(filtered) + page_size - 1) // page_size
        self.assertGreater(total_pages, 0, "Should calculate pages for filtered data")

        # Test data export with filters
        json_data = export_data_to_json(None, 'all_scores', filtered)
        self.assertEqual(len(json_data['data']), len(filtered))

    def test_performance_with_large_dataset(self):
        """Test performance with large dataset"""
        # Create large dataset (1000 records)
        for i in range(1000):
            data = {
                "timestamp": f"2025-11-{10 + (i % 20):02d} 10:00:00",
                "duration_seconds": 15.0,
                "total_operations": 1000000 + i * 1000,
                "ops_per_second": 100000.0 + i * 100,
                "num_threads": 4,
                "system": {
                    "platform": "Linux" if i % 2 == 0 else "Windows",
                    "processor_model": f"Test CPU {i % 50}",
                    "processor_frequency": "3.5GHz"
                }
            }
            filename = f"benchmark_results/large_{i:04d}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)

        # Measure load time
        start_time = time.time()
        scores = _get_all_valid_scores()
        load_time = time.time() - start_time

        self.assertEqual(len(scores), 1100)  # 100 + 1000 records
        self.assertLess(load_time, 5.0, "Should load large dataset quickly")

        # Measure filter time
        start_time = time.time()
        filtered = apply_all_filters(scores, "CPU 1", None, None, "Linux")
        filter_time = time.time() - start_time

        self.assertLess(filter_time, 2.0, "Should filter large dataset quickly")


if __name__ == "__main__":
    unittest.main()