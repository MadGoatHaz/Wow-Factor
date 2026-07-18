"""Tests for core/validation.py — input validation layer for benchmark parameters.

Covers:
  - Validation class: duration, threads, batch_runs (tuple return)
  - Module-level functions: duration, threads, batch_runs (exception raising)
  - Combined validators: validate_inputs, validate_batch_inputs
  - BenchmarkInputError raised correctly on invalid inputs
"""
import unittest
from unittest.mock import patch

from core.validation import Validation, validate_duration, validate_threads, validate_batch_runs
from core.validation import validate_inputs, validate_batch_inputs
from core.exceptions import BenchmarkInputError


class TestValidationDuration(unittest.TestCase):
    """Tests for duration validation (Validation class method)."""

    def setUp(self):
        self.v = Validation()

    def test_valid_duration_returns_int_and_none_error(self):
        value, err = self.v.validate_duration("15")
        self.assertEqual(value, 15)
        self.assertIsNone(err)

    def test_valid_duration_min_value(self):
        value, err = self.v.validate_duration("1")
        self.assertEqual(value, 1)
        self.assertIsNone(err)

    def test_valid_duration_large_value(self):
        value, err = self.v.validate_duration("3600")
        self.assertEqual(value, 3600)
        self.assertIsNone(err)

    def test_zero_duration_returns_error(self):
        value, err = self.v.validate_duration("0")
        self.assertIsNone(value)
        self.assertIn("greater than 0", err)

    def test_negative_duration_returns_error(self):
        value, err = self.v.validate_duration("-5")
        self.assertIsNone(value)
        self.assertIn("greater than 0", err)

    def test_empty_string_returns_error(self):
        value, err = self.v.validate_duration("")
        self.assertIsNone(value)
        self.assertIn("empty", err)

    def test_whitespace_only_returns_error(self):
        value, err = self.v.validate_duration("   ")
        self.assertIsNone(value)
        self.assertIn("empty", err)

    def test_non_integer_returns_error(self):
        value, err = self.v.validate_duration("abc")
        self.assertIsNone(value)
        self.assertIn("valid integer", err)

    def test_float_string_returns_error(self):
        value, err = self.v.validate_duration("3.14")
        self.assertIsNone(value)
        self.assertIn("valid integer", err)


class TestValidationThreads(unittest.TestCase):
    """Tests for thread count validation (Validation class method)."""

    def setUp(self):
        self.v = Validation()

    def test_valid_thread_count_one(self):
        value, err = self.v.validate_threads("1")
        self.assertEqual(value, 1)
        self.assertIsNone(err)

    @patch('core.validation._get_max_threads', return_value=8)
    def test_valid_thread_count_at_max(self, mock_max):
        value, err = self.v.validate_threads("8")
        self.assertEqual(value, 8)
        self.assertIsNone(err)

    @patch('core.validation._get_max_threads', return_value=8)
    def test_thread_count_exceeds_max(self, mock_max):
        value, err = self.v.validate_threads("9")
        self.assertIsNone(value)
        self.assertIn("must not exceed", err)

    def test_zero_threads_returns_error(self):
        value, err = self.v.validate_threads("0")
        self.assertIsNone(value)
        self.assertIn("at least 1", err)

    def test_negative_threads_returns_error(self):
        value, err = self.v.validate_threads("-1")
        self.assertIsNone(value)
        self.assertIn("at least 1", err)

    def test_empty_threads_returns_error(self):
        value, err = self.v.validate_threads("")
        self.assertIsNone(value)
        self.assertIn("empty", err)

    def test_non_integer_threads_returns_error(self):
        value, err = self.v.validate_threads("threads")
        self.assertIsNone(value)
        self.assertIn("valid integer", err)


class TestValidationBatchRuns(unittest.TestCase):
    """Tests for batch runs validation (Validation class method)."""

    def setUp(self):
        self.v = Validation()

    def test_valid_batch_runs_min(self):
        value, err = self.v.validate_batch_runs("2")
        self.assertEqual(value, 2)
        self.assertIsNone(err)

    def test_valid_batch_runs_max(self):
        value, err = self.v.validate_batch_runs("100")
        self.assertEqual(value, 100)
        self.assertIsNone(err)

    def test_valid_batch_runs_middle(self):
        value, err = self.v.validate_batch_runs("10")
        self.assertEqual(value, 10)
        self.assertIsNone(err)

    def test_batch_runs_below_min(self):
        value, err = self.v.validate_batch_runs("1")
        self.assertIsNone(value)
        self.assertIn("at least 2", err)

    def test_batch_runs_above_max(self):
        value, err = self.v.validate_batch_runs("101")
        self.assertIsNone(value)
        self.assertIn("must not exceed 100", err)

    def test_empty_batch_runs_returns_error(self):
        value, err = self.v.validate_batch_runs("")
        self.assertIsNone(value)
        self.assertIn("empty", err)

    def test_non_integer_batch_runs_returns_error(self):
        value, err = self.v.validate_batch_runs("runs")
        self.assertIsNone(value)
        self.assertIn("valid integer", err)


class TestModuleLevelValidation(unittest.TestCase):
    """Tests for module-level validation functions that raise exceptions."""

    def test_validate_duration_success(self):
        result = validate_duration("30")
        self.assertEqual(result, 30)

    def test_validate_duration_raises_on_zero(self):
        with self.assertRaises(BenchmarkInputError):
            validate_duration("0")

    def test_validate_duration_raises_on_negative(self):
        with self.assertRaises(BenchmarkInputError):
            validate_duration("-10")

    def test_validate_duration_raises_on_empty(self):
        with self.assertRaises(BenchmarkInputError):
            validate_duration("")

    def test_validate_duration_raises_on_non_integer(self):
        with self.assertRaises(BenchmarkInputError):
            validate_duration("hello")

    def test_validate_threads_success(self):
        result = validate_threads("1")
        self.assertEqual(result, 1)

    def test_validate_threads_raises_on_zero(self):
        with self.assertRaises(BenchmarkInputError):
            validate_threads("0")

    def test_validate_threads_raises_on_empty(self):
        with self.assertRaises(BenchmarkInputError):
            validate_threads("")

    @patch('core.validation._get_max_threads', return_value=4)
    def test_validate_threads_raises_on_exceed(self, mock_max):
        with self.assertRaises(BenchmarkInputError):
            validate_threads("5")

    def test_validate_batch_runs_success(self):
        result = validate_batch_runs("10")
        self.assertEqual(result, 10)

    def test_validate_batch_runs_raises_on_below_min(self):
        with self.assertRaises(BenchmarkInputError):
            validate_batch_runs("1")

    def test_validate_batch_runs_raises_on_above_max(self):
        with self.assertRaises(BenchmarkInputError):
            validate_batch_runs("200")


class TestCombinedValidators(unittest.TestCase):
    """Tests for validate_inputs and validate_batch_inputs."""

    def test_validate_inputs_success(self):
        result = validate_inputs("15", "2")
        self.assertEqual(result["duration"], 15)
        self.assertEqual(result["threads"], 2)

    def test_validate_inputs_raises_on_bad_duration(self):
        with self.assertRaises(BenchmarkInputError):
            validate_inputs("0", "2")

    def test_validate_inputs_raises_on_bad_threads(self):
        with self.assertRaises(BenchmarkInputError):
            validate_inputs("15", "0")

    def test_validate_batch_inputs_success(self):
        result = validate_batch_inputs("5", "15", "1")
        self.assertEqual(result["batch_runs"], 5)
        self.assertEqual(result["duration"], 15)
        self.assertEqual(result["threads"], 1)

    def test_validate_batch_inputs_raises_on_bad_runs(self):
        with self.assertRaises(BenchmarkInputError):
            validate_batch_inputs("1", "15", "1")

    def test_validate_batch_inputs_raises_on_bad_duration(self):
        with self.assertRaises(BenchmarkInputError):
            validate_batch_inputs("5", "0", "1")

    def test_validate_batch_inputs_raises_on_bad_threads(self):
        with self.assertRaises(BenchmarkInputError):
            validate_batch_inputs("5", "15", "0")


class TestBenchmarkInputError(unittest.TestCase):
    """Tests for BenchmarkInputError exception."""

    def test_is_subclass_of_benchmark_error(self):
        from core.exceptions import BenchmarkError
        self.assertTrue(issubclass(BenchmarkInputError, BenchmarkError))

    def test_can_carry_message(self):
        err = BenchmarkInputError("test message")
        self.assertEqual(str(err), "test message")


if __name__ == "__main__":
    unittest.main()