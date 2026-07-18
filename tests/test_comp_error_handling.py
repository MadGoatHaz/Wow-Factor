#!/usr/bin/env python3
"""
Error handling tests from the comprehensive test suite.
Tests invalid JSON, missing directories, malformed dates, and empty exports.
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
    export_data_to_json, _invalidate_all_cache, _cache
)


class TestErrorHandlingComprehensive(unittest.TestCase):
    """Test error handling and edge cases from comprehensive suite"""

    def setUp(self):
        """Set up test environment"""
        self.test_data_dir = tempfile.mkdtemp(prefix="wow_test_")
        self.original_dir = os.getcwd()
        os.chdir(self.test_data_dir)

        # Create benchmark results directory
        os.makedirs("benchmark_results", exist_ok=True)
        # Force clear cache
        _invalidate_all_cache()
        _cache.clear()

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_data_dir, ignore_errors=True)

    def test_invalid_json_files(self):
        """Test handling of invalid JSON files"""
        # Create invalid JSON file
        with open("benchmark_results/invalid.json", 'w') as f:
            f.write("{invalid json content")

        # Create valid JSON but missing required fields
        with open("benchmark_results/incomplete.json", 'w') as f:
            json.dump({"timestamp": "2025-11-20 10:00:00"}, f)

        # Should not crash and should return only valid scores
        scores = _get_all_valid_scores()
        self.assertEqual(len(scores), 0, "Should not load invalid files")

    def test_missing_directories(self):
        """Test handling of missing directories"""
        # Remove benchmark directory
        shutil.rmtree("benchmark_results", ignore_errors=True)

        # Should not crash
        scores = _get_all_valid_scores()
        self.assertEqual(len(scores), 0, "Should return empty list for missing directory")

    def test_malformed_dates(self):
        """Test handling of malformed dates in data"""
        # Create data with malformed date
        data = {
            "timestamp": "invalid-date-format",
            "duration_seconds": 15.0,
            "total_operations": 1000000,
            "ops_per_second": 100000.0,
            "num_threads": 4,
            "system": {
                "platform": "Linux",
                "processor_model": "Test CPU",
                "processor_frequency": "3.5GHz"
            }
        }

        with open("benchmark_results/malformed_date.json", 'w') as f:
            json.dump(data, f, indent=2)

        # Should handle malformed dates gracefully
        scores = _get_all_valid_scores()
        self.assertEqual(len(scores), 1, "Should load data with malformed date")

        # Date filtering should handle malformed dates
        start_date = parse_date("2025-11-20")
        end_date = parse_date("2025-11-25")
        filtered = apply_all_filters(scores, "", start_date, end_date, "")
        # Should not crash, result depends on implementation

    def test_export_with_no_data(self):
        """Test export functionality with no data"""
        # Should handle export with no data gracefully
        json_data = export_data_to_json(None, 'best_scores', [])
        self.assertEqual(len(json_data['data']), 0)

        # Test with None data
        json_data = export_data_to_json(None, 'best_scores', None)
        self.assertEqual(len(json_data['data']), 0)


if __name__ == "__main__":
    unittest.main()