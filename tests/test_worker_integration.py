#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test the actual integration with our modified code by creating a simple mock scenario
from core.benchmark import execute_single_benchmark_run
import time

def test_basic_functionality():
    """Test basic benchmark functionality"""
    print("Testing basic benchmark execution...")
    
    def progress_callback(total_ops, current_time, start_time):
        if total_ops % 10000 == 0:
            print(f"Progress: {total_ops} operations")
            
    try:
        result = execute_single_benchmark_run(duration=0.5, is_infinite=False, progress_callback=progress_callback)
        print("Benchmark completed successfully:")
        print(f"  Total ops: {result.get('total_operations', 0)}")
        print(f"  Duration: {result.get('duration_seconds', 0):.2f}s")
    except Exception as e:
        print(f"Benchmark failed with exception: {type(e).__name__}: {e}")
        assert False, f"Benchmark failed with exception: {type(e).__name__}: {e}"

if __name__ == "__main__":
    success = test_basic_functionality()
    if success:
        print("✓ Basic functionality works correctly")
    else:
        print("✗ Basic functionality has issues")