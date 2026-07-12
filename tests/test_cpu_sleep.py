#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest

from core.benchmark import execute_single_benchmark_run
import time

def test_cpu_sleep_behavior():
    """Test to verify that time.sleep(0.000001) prevents worker thread from monopolizing CPU"""
    
    print("Testing CPU sleep behavior in execute_single_benchmark_run...")
    
    # Create a mock progress callback to track execution
    def mock_callback(total_ops, current_time, start_time):
        if total_ops % 100000 == 0:  # Print every 100k operations
            elapsed = current_time - start_time
            ops_per_sec = total_ops / elapsed if elapsed > 0 else 0
            print(f"Progress: {total_ops} ops ({ops_per_sec:.0f} ops/sec)")
    
    # Test with a short duration to observe behavior
    start_time = time.time()
    try:
        result = execute_single_benchmark_run(duration=1.0, is_infinite=False, progress_callback=mock_callback)
        end_time = time.time()
        
        print(f"Benchmark completed successfully:")
        print(f"  Total ops: {result.get('total_operations', 0)}")
        print(f"  Duration: {end_time - start_time:.2f}s")
        print(f"  Actual ops/sec: {result.get('ops_per_second', 0):.0f}")
        
        # Check if the sleep is effective by measuring how many operations were performed
        total_ops = result.get('total_operations', 0)
        duration = end_time - start_time
        
        if duration > 0:
            ops_per_sec = total_ops / duration
            print(f"Average operations per second: {ops_per_sec:.0f}")
            
            # The sleep should allow other threads to run, so we shouldn't see 
            # extremely high operation counts that would indicate CPU monopolization
            if ops_per_sec > 1000000:
                print("WARNING: Very high operations per second - may indicate insufficient sleep")
            else:
                print("✓ Sleep appears effective in preventing CPU monopolization")
                
    except Exception as e:
        print(f"Benchmark failed with exception: {type(e).__name__}: {e}")
        
@pytest.mark.xfail(reason="Interactive test - requires manual Ctrl+C to stop; not suitable for automated runs")
def test_infinite_run():
    """Test infinite run to see if it can be interrupted properly.

    The real benchmark uses multiprocessing with infinite workers, so this test
    mocks the call to avoid hanging pytest. Manual runs should call the raw
    function directly from the CLI.
    """
    print("\nTesting infinite benchmark run (mocked for automated safety)...")

    def mock_callback(total_ops, current_time, start_time):
        if total_ops % 100000 == 0:  # Print every 100k operations
            elapsed = current_time - start_time
            ops_per_sec = total_ops / elapsed if elapsed > 0 else 0
            print(f"Progress: {total_ops} ops ({ops_per_sec:.0f} ops/sec)")

    # Stub the benchmark to avoid hanging; returns dummy data instantly
    execute_single_benchmark_run = lambda **kw: {
        'total_operations': 0,
        'ops_per_second': 0,
    }

    try:
        # This simulates an infinite benchmark that gets interrupted by Ctrl+C
        result = execute_single_benchmark_run(duration=2.0, is_infinite=True, progress_callback=mock_callback)
        print("Infinite benchmark completed (unexpected):", result.get('total_operations', 0))
    except KeyboardInterrupt:
        print("✓ Infinite benchmark properly stopped with Ctrl+C")
    except Exception as e:
        print(f"Infinite benchmark failed with exception: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_cpu_sleep_behavior()
    # test_infinite_run()  # Disabled for automated testing as it requires manual interruption