"""Tests for core.validation module."""

import multiprocessing
import pytest
from core.validation import Validation, MAX_BATCH_RUNS, MIN_BATCH_RUNS, DEFAULT_CPU_COUNT


class TestValidateDuration:
    """Tests for Validation.validate_duration."""

    def test_valid_positive_integer(self):
        value, err = Validation.validate_duration("15")
        assert value == 15
        assert err is None

    def test_valid_one(self):
        value, err = Validation.validate_duration("1")
        assert value == 1
        assert err is None

    def test_valid_large_number(self):
        value, err = Validation.validate_duration("99999")
        assert value == 99999
        assert err is None

    def test_zero_rejected(self):
        value, err = Validation.validate_duration("0")
        assert value == 0
        assert err is not None
        assert "greater than 0" in err

    def test_negative_rejected(self):
        value, err = Validation.validate_duration("-5")
        assert value == 0
        assert err is not None

    def test_empty_string_rejected(self):
        value, err = Validation.validate_duration("")
        assert value == 0
        assert err is not None

    def test_float_string_rejected(self):
        value, err = Validation.validate_duration("3.5")
        assert value == 0
        assert err is not None

    def test_non_numeric_rejected(self):
        value, err = Validation.validate_duration("abc")
        assert value == 0
        assert err is not None

    def test_whitespace_rejected(self):
        value, err = Validation.validate_duration("  ")
        assert value == 0
        assert err is not None


class TestValidateThreads:
    """Tests for Validation.validate_threads."""

    def test_valid_one(self):
        value, err = Validation.validate_threads("1")
        assert value == 1
        assert err is None

    def test_valid_cpu_count(self):
        value, err = Validation.validate_threads(str(DEFAULT_CPU_COUNT))
        assert value == DEFAULT_CPU_COUNT
        assert err is None

    def test_valid_mid_range(self):
        mid = DEFAULT_CPU_COUNT // 2
        value, err = Validation.validate_threads(str(mid))
        assert value == mid
        assert err is None

    def test_zero_rejected(self):
        value, err = Validation.validate_threads("0")
        assert value == 0
        assert err is not None
        assert "at least 1" in err

    def test_negative_rejected(self):
        value, err = Validation.validate_threads("-1")
        assert value == 0
        assert err is not None

    def test_exceeds_cpu_count_rejected(self):
        value, err = Validation.validate_threads(str(DEFAULT_CPU_COUNT + 1))
        assert value == 0
        assert err is not None
        assert "exceed" in err

    def test_empty_string_rejected(self):
        value, err = Validation.validate_threads("")
        assert value == 0
        assert err is not None

    def test_non_numeric_rejected(self):
        value, err = Validation.validate_threads("abc")
        assert value == 0
        assert err is not None

    def test_custom_max_threads_override(self):
        value, err = Validation.validate_threads("3", max_threads=5)
        assert value == 3
        assert err is None

    def test_custom_max_threads_rejected(self):
        value, err = Validation.validate_threads("6", max_threads=5)
        assert value == 0
        assert err is not None
        assert "5" in err


class TestValidateBatchRuns:
    """Tests for Validation.validate_batch_runs."""

    def test_valid_minimum(self):
        value, err = Validation.validate_batch_runs(str(MIN_BATCH_RUNS))
        assert value == MIN_BATCH_RUNS
        assert err is None

    def test_valid_maximum(self):
        value, err = Validation.validate_batch_runs(str(MAX_BATCH_RUNS))
        assert value == MAX_BATCH_RUNS
        assert err is None

    def test_valid_mid_range(self):
        value, err = Validation.validate_batch_runs("10")
        assert value == 10
        assert err is None

    def test_below_minimum_rejected(self):
        value, err = Validation.validate_batch_runs("1")
        assert value == 0
        assert err is not None
        assert str(MIN_BATCH_RUNS) in err

    def test_above_maximum_rejected(self):
        value, err = Validation.validate_batch_runs(str(MAX_BATCH_RUNS + 1))
        assert value == 0
        assert err is not None
        assert str(MAX_BATCH_RUNS) in err

    def test_empty_string_rejected(self):
        value, err = Validation.validate_batch_runs("")
        assert value == 0
        assert err is not None

    def test_non_numeric_rejected(self):
        value, err = Validation.validate_batch_runs("xyz")
        assert value == 0
        assert err is not None

    def test_zero_rejected(self):
        value, err = Validation.validate_batch_runs("0")
        assert value == 0
        assert err is not None


class TestConstants:
    """Tests for module-level constants."""

    def test_default_cpu_count_positive(self):
        assert DEFAULT_CPU_COUNT > 0

    def test_min_batch_runs_is_two(self):
        assert MIN_BATCH_RUNS == 2

    def test_max_batch_runs_is_100(self):
        assert MAX_BATCH_RUNS == 100

    def test_min_below_max(self):
        assert MIN_BATCH_RUNS < MAX_BATCH_RUNS