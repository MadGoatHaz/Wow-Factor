#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.benchmark import execute_single_benchmark_run
import time
import threading

def test_error_handling():
    """Test that our improved error handling works correctly"""
    
    print("Testing enhanced error handling...")
    
    # Create a mock progress callback that will cause an issue
    def mock_callback(total_ops, current_time, start_time):
        if total_ops > 1000:
            # Simulate an error condition to test our exception handling
            raise ValueError("Simulated benchmark error for testing")
            
    try:
        # This should trigger our enhanced error handling
        result = execute_single_benchmark_run(duration=0.5, is_infinite=False, progress_callback=mock_callback)
        print("Benchmark completed normally:", result.get('total_operations', 0))
    except Exception as e:
        print(f"Exception caught: {type(e).__name__}: {e}")
        
if __name__ == "__main__":
    test_error_handling()