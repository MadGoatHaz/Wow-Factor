#!/usr/bin/env python3
"""
Tests for results comparison tool.
"""

import unittest
import os
import tempfile
import shutil
import json


class TestResultsComparator(unittest.TestCase):
    """Test suite for ResultsComparator class."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_data_dir = tempfile.mkdtemp(prefix="wowfactor_test_")
        
        from core.comparator import ResultsComparator
        
        self.Comparator = ResultsComparator
        self.comparator = ResultsComparator(data_dir=self.test_data_dir)
    
    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_data_dir, ignore_errors=True)
    
    def test_get_available_results_empty(self) -> None:
        """Test getting available results when directory is empty."""
        results = self.comparator.get_available_results()
        self.assertEqual(results, [])
    
    def test_get_available_results_with_files(self) -> None:
        """Test getting available results with JSON files present."""
        # Create some test result files
        test_file1 = os.path.join(self.test_data_dir, "results_001.json")
        test_file2 = os.path.join(self.test_data_dir, "results_002.json")
        
        with open(test_file1, 'w') as f:
            json.dump({"ops_per_second": 1000}, f)
        with open(test_file2, 'w') as f:
            json.dump({"ops_per_second": 2000}, f)
        
        results = self.comparator.get_available_results()
        
        self.assertEqual(len(results), 2)
        self.assertIn("results_001.json", results)
        self.assertIn("results_002.json", results)
    
    def test_load_result_valid(self) -> None:
        """Test loading a valid result file."""
        test_file = os.path.join(self.test_data_dir, "valid_result.json")
        
        with open(test_file, 'w') as f:
            json.dump({
                "ops_per_second": 1500,
                "duration_seconds": 15,
                "total_operations": 22500
            }, f)
        
        result = self.comparator.load_result("valid_result.json")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["ops_per_second"], 1500)
    
    def test_load_result_invalid_json(self) -> None:
        """Test loading an invalid JSON file."""
        test_file = os.path.join(self.test_data_dir, "invalid.json")
        
        with open(test_file, 'w') as f:
            f.write("not valid json {")
        
        result = self.comparator.load_result("invalid.json")
        self.assertIsNone(result)
    
    def test_load_result_missing_fields(self) -> None:
        """Test loading a file missing required fields."""
        test_file = os.path.join(self.test_data_dir, "incomplete.json")
        
        with open(test_file, 'w') as f:
            json.dump({"ops_per_second": 1000}, f)  # Missing duration_seconds
        
        result = self.comparator.load_result("incomplete.json")
        self.assertIsNone(result)
    
    def test_compare_runs(self) -> None:
        """Test comparing two benchmark runs."""
        run1_file = os.path.join(self.test_data_dir, "run1.json")
        run2_file = os.path.join(self.test_data_dir, "run2.json")
        
        with open(run1_file, 'w') as f:
            json.dump({
                "ops_per_second": 1000,
                "duration_seconds": 15,
                "total_operations": 15000,
                "num_threads": 4,
                "system": {"processor_model": "Intel i7"}
            }, f)
        
        with open(run2_file, 'w') as f:
            json.dump({
                "ops_per_second": 1200,
                "duration_seconds": 15,
                "total_operations": 18000,
                "num_threads": 4,
                "system": {"processor_model": "Intel i7"}
            }, f)
        
        result = self.comparator.compare_runs("run1.json", "run2.json")
        
        self.assertIsNotNone(result)
        self.assertEqual(result.run1_name, "run1.json")
        self.assertEqual(result.run2_name, "run2.json")
        
        # Check metrics
        self.assertIn('ops_per_second', result.metrics)
        ops_metric = result.metrics['ops_per_second']
        self.assertEqual(ops_metric[0], 1000)  # Run 1 value
        self.assertEqual(ops_metric[1], 1200)  # Run 2 value
        self.assertAlmostEqual(ops_metric[2], 20.0, places=1)  # 20% improvement
    
    def test_compare_runs_different_threads(self) -> None:
        """Test comparing runs with different thread counts."""
        run1_file = os.path.join(self.test_data_dir, "run1.json")
        run2_file = os.path.join(self.test_data_dir, "run2.json")
        
        with open(run1_file, 'w') as f:
            json.dump({
                "ops_per_second": 1000,
                "duration_seconds": 15,
                "total_operations": 15000,
                "num_threads": 4
            }, f)
        
        with open(run2_file, 'w') as f:
            json.dump({
                "ops_per_second": 1000,
                "duration_seconds": 15,
                "total_operations": 15000,
                "num_threads": 8
            }, f)
        
        result = self.comparator.compare_runs("run1.json", "run2.json")
        
        self.assertIsNotNone(result)
        self.assertIn('num_threads', result.metrics)
        self.assertEqual(result.metrics['num_threads'], (4, 8, 0.0))
    
    def test_compare_multiple(self) -> None:
        """Test comparing multiple runs."""
        files = []
        for i in range(3):
            filepath = os.path.join(self.test_data_dir, f"run{i}.json")
            with open(filepath, 'w') as f:
                json.dump({"ops_per_second": (i + 1) * 1000}, f)
            files.append(f"run{i}.json")
        
        results = self.comparator.compare_multiple(files)
        
        # Should have 3 comparisons: (0,1), (0,2), (1,2)
        self.assertEqual(len(results), 3)
    
    def test_get_best_run(self) -> None:
        """Test getting the best performing run."""
        files = []
        for i, ops in enumerate([500, 1500, 1000]):
            filepath = os.path.join(self.test_data_dir, f"run{i}.json")
            with open(filepath, 'w') as f:
                json.dump({
                    "ops_per_second": ops,
                    "duration_seconds": 15,
                    "total_operations": 15000
                }, f)
            files.append(f"run{i}.json")
        
        best = self.comparator.get_best_run()
        
        self.assertEqual(best, "run1.json")  # 1500 is the highest
    
    def test_get_stats_for_run(self) -> None:
        """Test getting statistics for a specific run."""
        test_file = os.path.join(self.test_data_dir, "stats_test.json")
        
        with open(test_file, 'w') as f:
            json.dump({
                "ops_per_second": 2500,
                "duration_seconds": 30,
                "total_operations": 75000,
                "num_threads": 8,
                "system": {"processor_model": "AMD Ryzen"},
                "timestamp": "2026-04-03 12:00:00"
            }, f)
        
        stats = self.comparator.get_stats_for_run("stats_test.json")
        
        self.assertIsNotNone(stats)
        self.assertEqual(stats['filename'], "stats_test.json")
        self.assertEqual(stats['ops_per_second'], 2500)
        self.assertEqual(stats['cpu_model'], "AMD Ryzen")


if __name__ == "__main__":
    unittest.main()
