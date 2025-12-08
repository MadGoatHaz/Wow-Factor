#!/usr/bin/env python3
"""
Custom message classes for WowFactor TUI application.
These classes are used for communication between different components of the application.
"""

from textual.message import Message # Import Message for custom events


class BenchmarkProgress(Message):
    """Message for live progress updates from benchmark worker."""
    def __init__(self, total_ops: int, ops_per_second: float):
        super().__init__()
        self.total_ops = total_ops
        self.ops_per_second = ops_per_second


class BenchmarkCompletion(Message):
    """Message for when the benchmark worker completes."""
    def __init__(self, result_data: dict, interrupted: bool = False):
        super().__init__()
        self.result_data = result_data
        self.interrupted = interrupted


class BatchBenchmarkProgress(Message):
    """Message for live progress updates from individual benchmark run within a batch."""
    def __init__(self, batch_run_number: int, total_batch_runs: int, total_ops: int, ops_per_second: float):
        super().__init__()
        self.batch_run_number = batch_run_number
        self.total_batch_runs = total_batch_runs
        self.total_ops = total_ops
        self.ops_per_second = ops_per_second


class BatchBenchmarkCompletion(Message):
    """Message for when the entire batch benchmark worker completes."""
    def __init__(self, results: list, total_batch_runs: int, interrupted: bool = False):
        super().__init__()
        self.results = results
        self.total_batch_runs = total_batch_runs
        self.interrupted = interrupted


class CooldownMessage(Message):
    """Message for cooldown periods between batch runs."""
    def __init__(self, current_batch_run: int, total_batch_runs: int, cooldown_seconds: int):
        super().__init__()
        self.current_batch_run = current_batch_run
        self.total_batch_runs = total_batch_runs
        self.cooldown_seconds = cooldown_seconds


class DataLoadComplete(Message):
    """Message for when data loading completes successfully."""
    def __init__(self, data):
        super().__init__()
        self.data = data


class DataLoadError(Message):
    """Message for when data loading encounters an error."""
    def __init__(self):
        super().__init__()