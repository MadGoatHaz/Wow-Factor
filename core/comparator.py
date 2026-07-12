#!/usr/bin/env python3
"""
Results comparison tool for WowFactor TUI.
Allows comparing two benchmark runs side-by-side with percentage differences.
"""

from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache
from dataclasses import dataclass
import json
import os


@dataclass
class ComparisonResult:
    """Result of comparing two benchmark runs."""
    run1_name: str
    run2_name: str
    metrics: Dict[str, Tuple[float, float, float]]  # metric -> (run1_val, run2_val, diff_pct)
    
    def format_comparison(self) -> str:
        """Format comparison result as a readable string."""
        lines = [
            "=" * 60,
            f"RESULTS COMPARISON",
            "=" * 60,
            f"Run 1: {self.run1_name}",
            f"Run 2: {self.run2_name}",
            "",
            "METRIC              RUN 1           RUN 2           DIFF %"
        ]
        
        for metric, (val1, val2, diff) in self.metrics.items():
            if metric == "ops_per_second":
                # Format as thousands with commas
                line = f"{metric:20} {val1:>15,.0f}  {val2:>15,.0f}  {diff:+.1f}%"
            else:
                line = f"{metric:20} {val1:>15}  {val2:>15}  {diff:+.1f}%"
            lines.append(line)
        
        lines.extend([
            "",
            "=" * 60,
            "Legend: + = Run 2 is faster/better, - = Run 1 is faster/better",
            "=" * 60
        ])
        
        return "\n".join(lines)


class ResultsComparator:
    """
    Compares benchmark results from different runs.
    
    Loads results from JSON files and provides comparison functionality.
    """
    
    def __init__(self, data_dir: str = "benchmark_results") -> None:
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def get_available_results(self) -> List[str]:
        """Get list of available benchmark result files."""
        results = []
        if os.path.exists(self.data_dir):
            for filename in sorted(os.listdir(self.data_dir)):
                if filename.endswith('.json'):
                    results.append(filename)
        return results
    
    @lru_cache(maxsize=128)
    def load_result(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load a single benchmark result from file."""
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Validate required fields
            required_fields = ['ops_per_second', 'duration_seconds', 'total_operations']
            if not all(field in data for field in required_fields):
                return None
            
            return data
        except (json.JSONDecodeError, IOError):
            return None
    
    def compare_runs(
        self,
        run1_file: str,
        run2_file: str
    ) -> Optional[ComparisonResult]:
        """
        Compare two benchmark runs.
        
        Args:
            run1_file: Filename of first benchmark result
            run2_file: Filename of second benchmark result
            
        Returns:
            ComparisonResult with metrics and percentage differences,
            or None if comparison failed
        """
        data1 = self.load_result(run1_file)
        data2 = self.load_result(run2_file)
        
        if not data1 or not data2:
            return None
        
        # Extract metrics for comparison
        metrics = {}
        
        # Operations per second (higher is better)
        ops1 = data1.get('ops_per_second', 0)
        ops2 = data2.get('ops_per_second', 0)
        if ops1 > 0:
            diff_pct = ((ops2 - ops1) / ops1) * 100
            metrics['ops_per_second'] = (ops1, ops2, diff_pct)
        
        # Duration (lower is better for same workload)
        dur1 = data1.get('duration_seconds', 0)
        dur2 = data2.get('duration_seconds', 0)
        if dur1 > 0:
            diff_pct = ((dur2 - dur1) / dur1) * 100
            metrics['duration_seconds'] = (dur1, dur2, diff_pct)
        
        # Total operations (higher is better)
        total1 = data1.get('total_operations', 0)
        total2 = data2.get('total_operations', 0)
        if total1 > 0:
            diff_pct = ((total2 - total1) / total1) * 100
            metrics['total_operations'] = (total1, total2, diff_pct)
        
        # Number of threads
        threads1 = data1.get('num_threads', 1)
        threads2 = data2.get('num_threads', 1)
        metrics['num_threads'] = (threads1, threads2, 0.0)
        
        # System info comparison
        sys1 = data1.get('system', {})
        sys2 = data2.get('system', {})
        
        cpu1 = sys1.get('processor_model', 'Unknown')
        cpu2 = sys2.get('processor_model', 'Unknown')
        metrics['cpu_model'] = (cpu1, cpu2, 0.0)
        
        # Platform comparison
        plat1 = sys1.get('platform', 'Unknown')
        plat2 = sys2.get('platform', 'Unknown')
        metrics['platform'] = (plat1, plat2, 0.0)
        
        return ComparisonResult(
            run1_name=run1_file,
            run2_name=run2_file,
            metrics=metrics
        )
    
    def compare_multiple(
        self,
        files: List[str]
    ) -> Dict[Tuple[str, str], Optional[ComparisonResult]]:
        """
        Compare multiple benchmark runs against each other.
        
        Args:
            files: List of filenames to compare
            
        Returns:
            Dictionary mapping (file1, file2) tuples to ComparisonResults
        """
        results = {}
        
        for i in range(len(files)):
            for j in range(i + 1, len(files)):
                key = (files[i], files[j])
                results[key] = self.compare_runs(files[i], files[j])
        
        return results
    
    def get_best_run(self) -> Optional[str]:
        """Get the filename of the best performing benchmark run."""
        results = self.get_available_results()
        if not results:
            return None
        
        best_ops = 0
        best_file = None
        
        for filename in results:
            data = self.load_result(filename)
            if data and data.get('ops_per_second', 0) > best_ops:
                best_ops = data['ops_per_second']
                best_file = filename
        
        return best_file
    
    def get_stats_for_run(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific benchmark run."""
        data = self.load_result(filename)
        if not data:
            return None
        
        stats = {
            'filename': filename,
            'timestamp': data.get('timestamp', 'Unknown'),
            'ops_per_second': data.get('ops_per_second', 0),
            'duration_seconds': data.get('duration_seconds', 0),
            'total_operations': data.get('total_operations', 0),
            'num_threads': data.get('num_threads', 1),
            'cpu_model': data.get('system', {}).get('processor_model', 'Unknown'),
        }
        
        return stats
