#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.benchmark import execute_single_benchmark_run
import time
import threading

def test_worker_cancel_detection():
    """Test that we can properly detect when Worker.cancel() interrupts execution"""
    
    # This is a simple test to see how the exception handling works in our modified code
    print("Testing worker cancellation detection...")
    
    # Create a mock progress callback
    def mock_callback(total_ops, current_time, start_time):
        print(f"Progress: {total_ops} ops")
        
    try:
        # This should run for a short time and then be interrupted by Worker.cancel()
        result = execute_single_benchmark_run(duration=0.1, is_infinite=False, progress_callback=mock_callback)
        print("Benchmark completed normally:", result.get('total_operations', 0))
    except Exception as e:
        print(f"Exception caught: {type(e).__name__}: {e}")
        
if __name__ == "__main__":
    test_worker_cancel_detection()