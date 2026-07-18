"""Input validation layer for benchmark parameters."""

import multiprocessing

from core.exceptions import BenchmarkInputError


def _get_max_threads() -> int:
    """Return the maximum number of threads allowed for benchmarks."""
    return multiprocessing.cpu_count() or 1


class Validation:
    """
    Centralized input validation for benchmark parameters.

    All methods return a tuple of (validated_value, error_message).
    If validation succeeds, error_message is None.
    If validation fails, validated_value is None.
    """

    def validate_duration(self, value: str) -> tuple:
        """
        Validate the benchmark duration.

        Duration must be a positive integer (> 0).

        Args:
            value: Raw string from the input widget.

        Returns:
            Tuple of (duration_int, None) on success or (None, error_str) on failure.
        """
        if not value or not value.strip():
            return (None, "Duration cannot be empty.")
        try:
            duration = int(value)
        except ValueError:
            return (None, f"'{value}' is not a valid integer for duration.")
        if duration <= 0:
            return (None, "Duration must be greater than 0.")
        return (duration, None)

    def validate_threads(self, value: str) -> tuple:
        """
        Validate the thread count.

        Thread count must be an integer within [1, cpu_count()].

        Args:
            value: Raw string from the input widget.

        Returns:
            Tuple of (threads_int, None) on success or (None, error_str) on failure.
        """
        max_threads = _get_max_threads()
        if not value or not value.strip():
            return (None, "Thread count cannot be empty.")
        try:
            threads = int(value)
        except ValueError:
            return (None, f"'{value}' is not a valid integer for threads.")
        if threads < 1:
            return (None, "Thread count must be at least 1.")
        if threads > max_threads:
            return (None, f"Thread count must not exceed {max_threads} (CPU cores).")
        return (threads, None)

    def validate_batch_runs(self, value: str) -> tuple:
        """
        Validate the batch run count.

        Batch runs must be an integer within [2, 100].

        Args:
            value: Raw string from the input widget.

        Returns:
            Tuple of (batch_runs_int, None) on success or (None, error_str) on failure.
        """
        if not value or not value.strip():
            return (None, "Batch runs cannot be empty.")
        try:
            runs = int(value)
        except ValueError:
            return (None, f"'{value}' is not a valid integer for batch runs.")
        if runs < 2:
            return (None, "Batch runs must be at least 2.")
        if runs > 100:
            return (None, "Batch runs must not exceed 100.")
        return (runs, None)


# Module-level convenience functions that raise exceptions (for non-UI usage).
def validate_duration(value: str) -> int:
    """Validate duration, raising BenchmarkInputError on failure."""
    result, err = Validation().validate_duration(value)
    if err:
        raise BenchmarkInputError(err)
    return result


def validate_threads(value: str) -> int:
    """Validate threads, raising BenchmarkInputError on failure."""
    result, err = Validation().validate_threads(value)
    if err:
        raise BenchmarkInputError(err)
    return result


def validate_batch_runs(value: str) -> int:
    """Validate batch runs, raising BenchmarkInputError on failure."""
    result, err = Validation().validate_batch_runs(value)
    if err:
        raise BenchmarkInputError(err)
    return result


def validate_inputs(duration: str, threads: str) -> dict:
    """Validate duration and threads together, raising on first failure."""
    return {
        "duration": validate_duration(duration),
        "threads": validate_threads(threads),
    }


def validate_batch_inputs(batch_runs: str, duration: str, threads: str) -> dict:
    """Validate batch inputs together, raising on first failure."""
    return {
        "batch_runs": validate_batch_runs(batch_runs),
        "duration": validate_duration(duration),
        "threads": validate_threads(threads),
    }