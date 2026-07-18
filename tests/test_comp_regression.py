#!/usr/bin/env python3
"""
Regression tests from the comprehensive test suite.
Tests that original features still work: best scores, CPU comparison, cleanup, formatting.
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
    _get_all_valid_scores, get_best_score_per_machine, get_scores_for_cpu,
    cleanup_invalid_scores, format_large_number, _invalidate_all_cache, _cache
)


class TestRegressionComprehensive(unittest.TestCase):
    """Test that original features still work correctly from comprehensive suite"""

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
            if 'core.benchmark' in sys.modules:
                sys.modules['core.benchmark']._cache.clear()
        except Exception:
            pass

        # Create benchmark results directory
        os.makedirs("benchmark_results", exist_ok=True)

        # Create test data
        self._create_regression_test_data()

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_data_dir, ignore_errors=True)

    def _create_regression_test_data(self):
        """Create test data for regression testing"""
        for i in range(10):
            data = {
                "timestamp": f"2025-11-{20 + i:02d} 10:00:00",
                "duration_seconds": 15.0,
                "total_operations": 1000000 + i * 100000,
                "ops_per_second": 100000.0 + i * 10000,
                "num_threads": 4,
                "system": {
                    "platform": "Linux",
                    "processor_model": f"Test CPU Model {i}",
                    "processor_frequency": "3.5GHz"
                }
            }
            filename = f"benchmark_results/regression_test_{i:03d}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)

    def test_best_scores_per_machine(self):
        """Test best scores per machine functionality"""
        best_scores = get_best_score_per_machine()
        self.assertGreater(len(best_scores), 0, "Should get best scores")

        # Verify structure
        for score in best_scores:
            self.assertIn('system', score)
            self.assertIn('processor_model', score['system'])
            self.assertIn('ops_per_second', score)

    def test_cpu_comparison(self):
        """Test CPU comparison functionality"""
        # Get scores for specific CPU
        scores = get_scores_for_cpu("Test CPU Model 1")
        self.assertGreater(len(scores), 0, "Should get scores for specific CPU")

        for score in scores:
            self.assertEqual(score['system']['processor_model'], "Test CPU Model 1")

    def test_cleanup_invalid_scores(self):
        """Test cleanup of invalid scores"""
        # Create invalid files
        with open("benchmark_results/invalid1.json", 'w') as f:
            f.write("{invalid json")

        with open("benchmark_results/invalid2.json", 'w') as f:
            json.dump({"incomplete": "data"}, f)

        # Create valid file
        with open("benchmark_results/valid.json", 'w') as f:
            json.dump({
                "timestamp": "2025-11-20 10:00:00",
                "duration_seconds": 15.0,
                "total_operations": 1000000,
                "ops_per_second": 100000.0,
                "num_threads": 4,
                "system": {
                    "platform": "Linux",
                    "processor_model": "Test CPU",
                    "processor_frequency": "3.5GHz"
                }
            }, f)

        # Cleanup should remove 2 invalid files
        deleted = cleanup_invalid_scores()
        self.assertEqual(len(deleted), 2, "Should delete 2 invalid files")

        # Verify valid file still exists
        self.assertTrue(os.path.exists("benchmark_results/valid.json"))

    def test_format_large_number(self):
        """Test number formatting function"""
        self.assertEqual(format_large_number(500), "500.00")
        self.assertEqual(format_large_number(1500), "1.50K")
        self.assertEqual(format_large_number(1500000), "1.50M")
        self.assertEqual(format_large_number(1500000000), "1500.00M")


if __name__ == "__main__":
    unittest.main()