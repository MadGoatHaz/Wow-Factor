"""WowFactor input validation layer for benchmark duration and thread inputs.

Provides pure validation functions that return (value, error_message) tuples.
Used by the benchmark UI screens to validate user input both inline and
before starting benchmark runs.
"""

from __future__ import annotations

import multiprocessing

MAX_BATCH_RUNS: int = 100
MIN_BATCH_RUNS: int = 2
DEFAULT_CPU_COUNT: int = multiprocessing.cpu_count()


class Validation:
    """Pure validation utilities for benchmark input fields."""

    @staticmethod
    def validate_duration(duration_str: str) -> tuple[int, str | None]:
        """Validate a benchmark duration string.

        Duration must be a positive integer (> 0).

        Args:
            duration_str: Raw string from the input field.

        Returns:
            Tuple of (validated_duration, error_message_or_None).
        """
        if not duration_str:
            return (0, "Duration is required.")
        try:
            duration = int(duration_str)
        except (ValueError, OverflowError):
            return (0, "Duration must be a positive integer.")
        if duration <= 0:
            return (0, "Duration must be greater than 0.")
        return (duration, None)

    @staticmethod
    def validate_threads(threads_str: str, max_threads: int | None = None) -> tuple[int, str | None]:
        """Validate a thread count string.

        Thread count must be an integer within [1, cpu_count()].

        Args:
            threads_str: Raw string from the input field.
            max_threads: Optional override for maximum threads (defaults to cpu_count).

        Returns:
            Tuple of (validated_threads, error_message_or_None).
        """
        if not threads_str:
            return (0, "Thread count is required.")
        try:
            threads = int(threads_str)
        except (ValueError, OverflowError):
            return (0, "Thread count must be a positive integer.")
        limit = max_threads if max_threads is not None else DEFAULT_CPU_COUNT
        if threads < 1:
            return (0, "Thread count must be at least 1.")
        if threads > limit:
            return (0, f"Thread count cannot exceed {limit} (CPU cores).")
        return (threads, None)

    @staticmethod
    def validate_batch_runs(runs_str: str) -> tuple[int, str | None]:
        """Validate a batch runs count string.

        Batch runs must be an integer within [2, 100].

        Args:
            runs_str: Raw string from the input field.

        Returns:
            Tuple of (validated_runs, error_message_or_None).
        """
        if not runs_str:
            return (0, "Batch runs is required.")
        try:
            runs = int(runs_str)
        except (ValueError, OverflowError):
            return (0, "Batch runs must be an integer.")
        if runs < MIN_BATCH_RUNS:
            return (0, f"Batch runs must be at least {MIN_BATCH_RUNS}.")
        if runs > MAX_BATCH_RUNS:
            return (0, f"Batch runs cannot exceed {MAX_BATCH_RUNS}.")
        return (runs, None)