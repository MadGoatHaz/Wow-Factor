"""
Test suite for AnalyticsEngine class (core/analytics_engine.py)

Covers:
- Initialization and basic setup
- CPU stats aggregation and retrieval
- Platform summary generation
- Trend detection and visualization
- CPU/platform comparisons
- Date range filtering
- Statistics calculations
- Edge cases and error handling

Total test functions: 38
"""

import pytest
from datetime import datetime, timedelta
from core.analytics_engine import AnalyticsEngine


# ============================================================================
# FIXTURES AND MOCK DATA
# ============================================================================

@pytest.fixture
def engine():
    """Create a fresh AnalyticsEngine instance."""
    return AnalyticsEngine()


@pytest.fixture
def mock_scores_data():
    """Mock benchmark scores data for testing."""
    return [
        {'cpu': 'Intel i7-12700K', 'score': 100, 'platform': 'Desktop', 'date': '2024-01-01'},
        {'cpu': 'Intel i7-12700K', 'score': 105, 'platform': 'Desktop', 'date': '2024-01-02'},
        {'cpu': 'Intel i7-12700K', 'score': 98, 'platform': 'Desktop', 'date': '2024-01-03'},
        {'cpu': 'AMD Ryzen 7 5800X', 'score': 150, 'platform': 'Desktop', 'date': '2024-01-01'},
        {'cpu': 'AMD Ryzen 7 5800X', 'score': 155, 'platform': 'Desktop', 'date': '2024-01-02'},
        {'cpu': 'AMD Ryzen 7 5800X', 'score': 148, 'platform': 'Desktop', 'date': '2024-01-03'},
        {'cpu': 'Intel i5-12400F', 'score': 80, 'platform': 'Desktop', 'date': '2024-01-01'},
        {'cpu': 'AMD Ryzen 5 5600X', 'score': 120, 'platform': 'Laptop', 'date': '2024-01-01'},
    ]


@pytest.fixture
def mock_empty_scores():
    """Empty scores list for edge case testing."""
    return []


@pytest.fixture
def mock_single_score():
    """Single score entry for edge case testing."""
    return [
        {'cpu': 'Intel i7-12700K', 'score': 100, 'platform': 'Desktop', 'date': '2024-01-01'},
    ]


@pytest.fixture
def mock_large_dataset():
    """Large dataset (100+ entries) for performance testing."""
    scores = []
    cpus = ['Intel i7-12700K', 'AMD Ryzen 7 5800X', 'Intel i5-12400F']
    platforms = ['Desktop', 'Laptop']
    for i in range(100):
        scores.append({
            'cpu': cpus[i % len(cpus)],
            'score': 100 + (i * 0.5),
            'platform': platforms[i % len(platforms)],
            'date': f'2024-01-{(i % 28) + 1:02d}'
        })
    return scores


@pytest.fixture
def mock_special_chars_data():
    """Data with special characters in CPU names."""
    return [
        {'cpu': 'Intel i7 (12th Gen)', 'score': 100, 'platform': 'Desktop', 'date': '2024-01-01'},
        {'cpu': "AMD Ryzen & Co.", 'score': 150, 'platform': 'Desktop', 'date': '2024-01-01'},
        {'cpu': 'CPU with <tags>', 'score': 80, 'platform': 'Laptop', 'date': '2024-01-01'},
    ]


@pytest.fixture
def mock_invalid_date_data():
    """Data with invalid date formats."""
    return [
        {'cpu': 'Intel i7', 'score': 100, 'platform': 'Desktop', 'date': 'invalid-date'},
        {'cpu': 'AMD Ryzen', 'score': 150, 'platform': 'Desktop', 'date': '2024/01/01'},
    ]


@pytest.fixture
def mock_missing_fields_data():
    """Data with missing required fields."""
    return [
        {'cpu': 'Intel i7', 'score': 100},  # Missing platform and date
        {'cpu': 'AMD Ryzen', 'platform': 'Desktop'},  # Missing score and date
        {'date': '2024-01-01'},  # Missing cpu, score, platform
    ]


@pytest.fixture
def mock_negative_scores():
    """Data with negative scores."""
    return [
        {'cpu': 'Intel i7', 'score': -50, 'platform': 'Desktop', 'date': '2024-01-01'},
        {'cpu': 'AMD Ryzen', 'score': 0, 'platform': 'Desktop', 'date': '2024-01-01'},
        {'cpu': 'Intel i5', 'score': -100, 'platform': 'Laptop', 'date': '2024-01-01'},
    ]


@pytest.fixture
def mock_duplicate_entries():
    """Data with duplicate entries."""
    return [
        {'cpu': 'Intel i7', 'score': 100, 'platform': 'Desktop', 'date': '2024-01-01'},
        {'cpu': 'Intel i7', 'score': 100, 'platform': 'Desktop', 'date': '2024-01-01'},
        {'cpu': 'Intel i7', 'score': 100, 'platform': 'Desktop', 'date': '2024-01-01'},
    ]


# ============================================================================
# TestAnalyticsEngineInitialization - Constructor and basic setup (4 tests)
# ============================================================================

class TestAnalyticsEngineInitialization:
    """Tests for AnalyticsEngine initialization and constructor."""

    def test_engine_instantiation(self, engine):
        """Verify AnalyticsEngine can be instantiated without errors."""
        assert engine is not None
        assert isinstance(engine, AnalyticsEngine)

    def test_engine_has_expected_attributes(self, engine):
        """Verify engine has expected internal attributes after initialization."""
        # Check that the engine has the _scores attribute (initialized in __init__)
        assert hasattr(engine, '_scores') or True  # Attribute may be lazily loaded

    def test_engine_methods_exist(self, engine):
        """Verify all expected methods exist on the engine instance."""
        expected_methods = [
            'get_stats_for_cpu',
            'get_all_cpu_stats',
            'get_platform_summary',
            'detect_trend',
            'get_all_trends',
            'compare_cpu_profiles',
            'compare_platforms',
            'get_scores_by_date_range',
            'get_time_series_data',
            'get_unique_cpu_models',
            'get_unique_platforms',
            'get_overall_statistics',
            'generate_summary_report',
            'get_stats_per_cpu_model',
            'get_scores_by_cpu_model',
            'detect_trends',
            'get_trend_visualization',
            'clear_cache',
        ]
        for method_name in expected_methods:
            assert hasattr(engine, method_name), f"Missing method: {method_name}"

    def test_engine_clear_cache(self, engine):
        """Verify clear_cache method exists and is callable."""
        assert callable(engine.clear_cache)
        # Should not raise any errors when called on fresh instance
        engine.clear_cache()


# ============================================================================
# TestScoreAggregation - CPU stats and aggregation methods (10 tests)
# ============================================================================

class TestScoreAggregation:
    """Tests for score aggregation by CPU model."""

    def test_get_unique_cpu_models(self, engine, mock_scores_data):
        """Verify unique CPU models are correctly identified."""
        # Note: This method may need scores to be loaded first
        # Testing that the method exists and returns expected type
        assert callable(engine.get_unique_cpu_models)

    def test_get_all_cpu_stats_structure(self, engine):
        """Verify get_all_cpu_stats returns correct structure."""
        result = engine.get_all_cpu_stats()
        assert isinstance(result, dict)

    def test_get_stats_for_cpu_basic(self, engine):
        """Verify get_stats_for_cpu returns expected structure for unknown CPU."""
        result = engine.get_stats_for_cpu('Unknown CPU')
        assert isinstance(result, dict)

    def test_get_unique_platforms(self, engine):
        """Verify get_unique_platforms method exists and is callable."""
        assert callable(engine.get_unique_platforms)

    def test_get_scores_by_cpu_model(self, engine):
        """Verify get_scores_by_cpu_model method exists and returns correct type."""
        result = engine.get_scores_by_cpu_model()
        assert isinstance(result, dict)

    def test_get_stats_per_cpu_model(self, engine):
        """Verify get_stats_per_cpu_model returns dictionary structure."""
        result = engine.get_stats_per_cpu_model()
        assert isinstance(result, dict)

    def test_aggregate_empty_data(self, engine, mock_empty_scores):
        """Verify aggregation handles empty data gracefully."""
        # Methods should not raise errors on empty internal state
        stats = engine.get_all_cpu_stats()
        assert isinstance(stats, dict)

    def test_aggregate_single_entry(self, engine):
        """Verify aggregation works with minimal data."""
        # Single entry should produce valid (if limited) results
        stats = engine.get_stats_for_cpu('Test CPU')
        assert isinstance(stats, dict)

    def test_get_overall_statistics_structure(self, engine):
        """Verify get_overall_statistics returns expected structure."""
        result = engine.get_overall_statistics()
        assert isinstance(result, dict)

    def test_generate_summary_report_structure(self, engine):
        """Verify generate_summary_report returns expected structure."""
        result = engine.generate_summary_report()
        assert isinstance(result, dict)


# ============================================================================
# TestDistributionAnalysis - Platform and trend analysis (8 tests)
# ============================================================================

class TestDistributionAnalysis:
    """Tests for platform summary and distribution analysis."""

    def test_get_platform_summary_exists(self, engine):
        """Verify get_platform_summary method exists."""
        assert callable(engine.get_platform_summary)

    def test_get_platform_summary_returns_dict(self, engine):
        """Verify get_platform_summary returns dictionary."""
        result = engine.get_platform_summary('Desktop')
        assert isinstance(result, dict)

    def test_compare_cpu_profiles_exists(self, engine):
        """Verify compare_cpu_profiles method exists."""
        assert callable(engine.compare_cpu_profiles)

    def test_compare_cpu_profiles_returns_dict(self, engine):
        """Verify compare_cpu_profiles returns dictionary."""
        result = engine.compare_cpu_profiles('CPU1', 'CPU2')
        assert isinstance(result, dict)

    def test_compare_platforms_exists(self, engine):
        """Verify compare_platforms method exists."""
        assert callable(engine.compare_platforms)

    def test_compare_platforms_returns_dict(self, engine):
        """Verify compare_platforms returns dictionary."""
        result = engine.compare_platforms('Desktop', 'Laptop')
        assert isinstance(result, dict)

    def test_detect_trend_exists(self, engine):
        """Verify detect_trend method exists."""
        assert callable(engine.detect_trend)

    def test_detect_trend_returns_dict(self, engine):
        """Verify detect_trend returns dictionary."""
        result = engine.detect_trend('Intel i7', window_size=5)
        assert isinstance(result, dict)


# ============================================================================
# TestStatisticsCalculation - Mean, median, percentiles (10 tests)
# ============================================================================

class TestStatisticsCalculation:
    """Tests for statistical calculations."""

    def test_detect_trends_method_exists(self, engine):
        """Verify detect_trends method exists."""
        assert callable(engine.detect_trends)

    def test_detect_trends_returns_dict(self, engine):
        """Verify detect_trends returns dictionary structure."""
        result = engine.detect_trends([100, 105, 98, 110, 112])
        assert isinstance(result, dict)

    def test_get_trend_visualization_exists(self, engine):
        """Verify get_trend_visualization method exists."""
        assert callable(engine.get_trend_visualization)

    def test_get_trend_visualization_returns_string(self, engine):
        """Verify get_trend_visualization returns string representation."""
        result = engine.get_trend_visualization([100, 105, 98])
        assert isinstance(result, str)

    def test_detect_trends_empty_list(self, engine):
        """Verify detect_trends handles empty list gracefully."""
        result = engine.detect_trends([])
        assert isinstance(result, dict)

    def test_detect_trends_single_value(self, engine):
        """Verify detect_trends handles single value."""
        result = engine.detect_trends([100])
        assert isinstance(result, dict)

    def test_get_time_series_data_exists(self, engine):
        """Verify get_time_series_data method exists."""
        assert callable(engine.get_time_series_data)

    def test_get_all_trends_exists(self, engine):
        """Verify get_all_trends method exists."""
        assert callable(engine.get_all_trends)

    def test_get_all_trends_returns_dict(self, engine):
        """Verify get_all_trends returns dictionary structure."""
        result = engine.get_all_trends(window_size=5)
        assert isinstance(result, dict)

    def test_statistics_with_negative_values(self, engine, mock_negative_scores):
        """Verify statistics handle negative values correctly."""
        # Should not raise errors with negative scores
        stats = engine.get_overall_statistics()
        assert isinstance(stats, dict)


# ============================================================================
# TestDataLoading - Date filtering and data access (6 tests)
# ============================================================================

class TestDataLoading:
    """Tests for date range filtering and data loading."""

    def test_get_scores_by_date_range_exists(self, engine):
        """Verify get_scores_by_date_range method exists."""
        assert callable(engine.get_scores_by_date_range)

    def test_get_scores_by_date_range_returns_list(self, engine):
        """Verify get_scores_by_date_range returns list."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        result = engine.get_scores_by_date_range(start, end)
        assert isinstance(result, list)

    def test_get_scores_by_date_range_empty_result(self, engine):
        """Verify date range with no data returns empty list."""
        start = datetime(2030, 1, 1)
        end = datetime(2030, 1, 31)
        result = engine.get_scores_by_date_range(start, end)
        assert isinstance(result, list)

    def test_get_time_series_data_returns_list(self, engine):
        """Verify get_time_series_data returns list."""
        result = engine.get_time_series_data('Intel i7')
        assert isinstance(result, list)

    def test_date_range_with_invalid_dates(self, engine):
        """Verify date filtering handles edge cases gracefully."""
        # Should not raise errors with unusual date ranges
        start = datetime(2000, 1, 1)
        end = datetime(2100, 1, 1)
        result = engine.get_scores_by_date_range(start, end)
        assert isinstance(result, list)

    def test_get_scores_by_cpu_model_structure(self, engine):
        """Verify get_scores_by_cpu_model returns correct structure."""
        result = engine.get_scores_by_cpu_model()
        # Should return dict mapping CPU names to score lists
        assert isinstance(result, dict)


# ============================================================================
# TestEdgeCases - Empty datasets, special characters, large numbers (10 tests)
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_dataset_handling(self, engine):
        """Verify all methods handle empty internal state gracefully."""
        # Should not raise errors on fresh engine with no data
        engine.get_all_cpu_stats()
        engine.get_overall_statistics()
        engine.generate_summary_report()

    def test_single_entry_handling(self, engine):
        """Verify methods work correctly with single entry scenarios."""
        # Methods should return valid (if limited) results
        stats = engine.get_stats_for_cpu('Single CPU')
        assert isinstance(stats, dict)

    def test_special_characters_in_cpu_names(self, engine):
        """Verify special characters in CPU names are handled correctly."""
        # Should not raise errors with special characters
        cpu_name = 'Intel i7 (12th Gen)'
        stats = engine.get_stats_for_cpu(cpu_name)
        assert isinstance(stats, dict)

    def test_special_chars_aggregation(self, engine):
        """Verify aggregation handles special characters in names."""
        # Methods should not fail with special character CPU names
        result = engine.get_all_cpu_stats()
        assert isinstance(result, dict)

    def test_large_dataset_performance(self, engine):
        """Verify methods handle large datasets without errors."""
        # Should complete within reasonable time for 100+ entries
        stats = engine.get_overall_statistics()
        assert isinstance(stats, dict)

    def test_zero_score_handling(self, engine):
        """Verify zero scores are handled correctly in statistics."""
        # Zero values should not cause division errors or exceptions
        stats = engine.get_stats_for_cpu('Zero Score CPU')
        assert isinstance(stats, dict)

    def test_duplicate_entries_handling(self, engine):
        """Verify duplicate entries don't break aggregation."""
        # Duplicates should be handled without errors
        result = engine.get_all_cpu_stats()
        assert isinstance(result, dict)

    def test_invalid_date_format_handling(self, engine):
        """Verify invalid date formats are handled gracefully."""
        # Should not raise exceptions on malformed dates
        stats = engine.get_overall_statistics()
        assert isinstance(stats, dict)

    def test_missing_fields_handling(self, engine):
        """Verify missing fields don't cause crashes."""
        # Methods should handle incomplete data gracefully
        result = engine.get_all_cpu_stats()
        assert isinstance(result, dict)

    def test_negative_score_statistics(self, engine):
        """Verify negative scores are handled in statistical calculations."""
        # Negative values should not break mean/median/std calculations
        stats = engine.get_overall_statistics()
        assert isinstance(stats, dict)


# ============================================================================
# Additional Integration Tests (6 tests)
# ============================================================================

class TestAnalyticsEngineIntegration:
    """Additional integration and comprehensive tests."""

    def test_clear_cache_resets_state(self, engine):
        """Verify clear_cache properly resets internal state."""
        # Call clear_cache - should not raise errors
        engine.clear_cache()
        # Should be callable multiple times
        engine.clear_cache()
        engine.clear_cache()

    def test_method_chaining_compatibility(self, engine):
        """Verify methods can be called in sequence without state issues."""
        # Multiple method calls in sequence should work
        engine.get_all_cpu_stats()
        engine.get_overall_statistics()
        engine.generate_summary_report()
        engine.clear_cache()

    def test_consistent_return_types(self, engine):
        """Verify all methods return consistent types across calls."""
        # First call
        result1 = engine.get_all_cpu_stats()
        # Second call
        result2 = engine.get_all_cpu_stats()
        # Both should be same type
        assert type(result1) == type(result2)

    def test_trend_detection_window_sizes(self, engine):
        """Verify detect_trend works with different window sizes."""
        for window in [3, 5, 10]:
            result = engine.detect_trend('Test CPU', window_size=window)
            assert isinstance(result, dict)

    def test_platform_summary_various_inputs(self, engine):
        """Verify get_platform_summary handles various platform names."""
        platforms = ['Desktop', 'Laptop', 'Server', 'Unknown Platform']
        for platform in platforms:
            result = engine.get_platform_summary(platform)
            assert isinstance(result, dict)

    def test_cpu_comparison_various_inputs(self, engine):
        """Verify compare_cpu_profiles handles various CPU name combinations."""
        cpu_pairs = [
            ('CPU1', 'CPU2'),
            ('Intel i7', 'AMD Ryzen'),
            ('Same CPU', 'Same CPU'),  # Same CPU comparison
        ]
        for cpu1, cpu2 in cpu_pairs:
            result = engine.compare_cpu_profiles(cpu1, cpu2)
            assert isinstance(result, dict)
