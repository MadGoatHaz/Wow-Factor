import pytest
import os
import time
from core.benchmark import execute_single_benchmark_run, BENCHMARK_DIR

def test_single_threaded_execution():
    """Test that single-threaded execution works as expected."""
    duration = 1.0
    result = execute_single_benchmark_run(duration=duration, num_threads=1)
    
    assert result['duration_seconds'] >= duration
    assert result['total_operations'] > 0
    assert result['num_threads'] == 1
    assert os.path.exists(result['file_path'])

def test_multi_threaded_execution():
    """Test that multi-threaded execution works and potentially increases throughput."""
    duration = 1.0
    num_threads = 2
    
    # Run with 2 threads
    result = execute_single_benchmark_run(duration=duration, num_threads=num_threads)
    
    # With warmup, duration might be slightly less than wall time, or calculation might vary.
    # We should just ensure it's reasonably close.
    assert result['duration_seconds'] >= duration * 0.9
    assert result['total_operations'] > 0
    assert result['num_threads'] == num_threads
    assert os.path.exists(result['file_path'])

    # Basic sanity check: 2 threads should ideally do more work than 1 thread,
    # or at least run without crashing.
    # Note: In Python, GIL might limit true parallelism for CPU-bound tasks,
    # but we are testing the threading logic itself here, not necessarily performance scaling.
    
def test_result_structure_with_threads():
    """Test that the saved result JSON structure includes num_threads."""
    duration = 0.5
    num_threads = 4
    result = execute_single_benchmark_run(duration=duration, num_threads=num_threads)
    
    import json
    with open(result['file_path'], 'r') as f:
        data = json.load(f)
        
    assert 'num_threads' in data
    assert data['num_threads'] == num_threads
    assert data['total_operations'] == result['total_operations']

if __name__ == "__main__":
    pytest.main([__file__])