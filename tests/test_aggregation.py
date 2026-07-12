#!/usr/bin/env python3
"""
Tests for benchmark aggregation functions.
Tests aggregate_scores_by_cpu and get_score_distribution from core.benchmark.
"""

import unittest
from typing import List, Dict, Any


class TestAggregationFunctions(unittest.TestCase):
    """Test suite for aggregation functions."""

    def setUp(self) -> None:
        """Set up test data before each test."""
        # Import inside setUp to ensure proper module loading
        from core.benchmark import aggregate_scores_by_cpu, get_score_distribution
        
        self.aggregate_scores_by_cpu = aggregate_scores_by_cpu
        self.get_score_distribution = get_score_distribution

    def test_aggregate_scores_by_cpu_empty_data(self) -> None:
        """Test aggregation with empty data."""
        result = self.aggregate_scores_by_cpu([])
        self.assertEqual(result, ([], []))

    def test_aggregate_scores_by_cpu_single_score(self) -> None:
        """Test aggregation with single score."""
        data: List[Dict[str, Any]] = [
            {"system": {"processor_model": "Intel i7"}, "ops_per_second": 1000.0}
        ]
        result = self.aggregate_scores_by_cpu(data)
        self.assertEqual(result, (["Intel i7"], [1000.0]))

    def test_aggregate_scores_by_cpu_multiple_same_cpu(self) -> None:
        """Test aggregation with multiple runs on same CPU."""
        data: List[Dict[str, Any]] = [
            {"system": {"processor_model": "Intel i7"}, "ops_per_second": 1000.0},
            {"system": {"processor_model": "Intel i7"}, "ops_per_second": 2000.0},
            {"system": {"processor_model": "Intel i7"}, "ops_per_second": 3000.0},
        ]
        result = self.aggregate_scores_by_cpu(data)
        # Should return average: (1000 + 2000 + 3000) / 3 = 2000
        self.assertEqual(result, (["Intel i7"], [2000.0]))

    def test_aggregate_scores_by_cpu_multiple_different_cpus(self) -> None:
        """Test aggregation with multiple different CPUs."""
        data: List[Dict[str, Any]] = [
            {"system": {"processor_model": "Intel i7"}, "ops_per_second": 1000.0},
            {"system": {"processor_model": "AMD Ryzen"}, "ops_per_second": 2000.0},
            {"system": {"processor_model": "Intel i7"}, "ops_per_second": 4000.0},
        ]
        result = self.aggregate_scores_by_cpu(data)
        # Intel i7: (1000 + 4000) / 2 = 2500
        # AMD Ryzen: 2000 / 1 = 2000
        cpus, scores = result
        self.assertEqual(len(cpus), 2)
        self.assertEqual(len(scores), 2)

    def test_aggregate_scores_by_cpu_missing_processor_model(self) -> None:
        """Test aggregation with missing processor model."""
        data: List[Dict[str, Any]] = [
            {"ops_per_second": 1000.0},  # Missing system.processor_model
        ]
        result = self.aggregate_scores_by_cpu(data)
        # Should handle gracefully - likely return empty or N/A
        cpus, scores = result
        self.assertEqual(len(cpus), len(scores))

    def test_get_score_distribution_empty_data(self) -> None:
        """Test distribution with empty data."""
        result = self.get_score_distribution([])
        self.assertEqual(result, ([], []))

    def test_get_score_distribution_single_score(self) -> None:
        """Test distribution with single score."""
        data: List[Dict[str, Any]] = [
            {"ops_per_second": 1000.0}
        ]
        result = self.get_score_distribution(data)
        bins, counts = result
        # Should have at least one bin
        self.assertGreater(len(bins), 0)
        self.assertGreater(len(counts), 0)

    def test_get_score_distribution_multiple_scores(self) -> None:
        """Test distribution with multiple scores."""
        data: List[Dict[str, Any]] = [
            {"ops_per_second": float(i * 1000)} for i in range(1, 21)
        ]
        result = self.get_score_distribution(data)
        bins, counts = result
        # Should have bins with counts
        self.assertGreater(len(bins), 0)
        self.assertEqual(sum(counts), len(data))

    def test_get_score_distribution_with_custom_bin_size(self) -> None:
        """Test distribution with custom bin size."""
        data: List[Dict[str, Any]] = [
            {"ops_per_second": float(i * 500)} for i in range(1, 21)
        ]
        result = self.get_score_distribution(data, bin_size=1000)
        bins, counts = result
        # With bin_size=1000 and data from 500-10000, should have fewer bins
        self.assertGreater(len(bins), 0)


if __name__ == "__main__":
    unittest.main()
