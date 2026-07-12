# wow_analytics_engine.py
# Advanced Analytics Engine for Benchmark Data Analysis
# Provides statistical summaries, trend detection, and comparative analysis

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import statistics

from core.benchmark import _get_all_valid_scores, BENCHMARK_DIR


class AnalyticsEngine:
    """
    Advanced analytics engine for processing and analyzing benchmark results.
    Provides statistical summaries, trend detection, and comparative analysis.
    """
    
    def __init__(self) -> None:
        """Initialize the analytics engine."""
        self._scores_cache: Optional[List[Dict]] = None
    
    def _load_scores(self) -> List[Dict]:
        """Load all valid benchmark scores from disk."""
        if self._scores_cache is None:
            self._scores_cache = _get_all_valid_scores()
        return self._scores_cache
    
    # ==================== STATISTICAL SUMMARIES ====================
    
    def get_stats_for_cpu(self, cpu_model: str) -> Dict[str, Any]:
        """
        Calculate comprehensive statistics for a specific CPU model.
        
        Returns:
            Dictionary containing mean, median, mode, std dev, min, max,
            count of samples, and raw score list.
        """
        scores = self._load_scores()
        cpu_scores = [s['ops_per_second'] for s in scores 
                      if s.get('system', {}).get('processor_model') == cpu_model]
        
        if not cpu_scores:
            return {'error': f'No data found for CPU: {cpu_model}'}
        
        # Calculate all statistics
        mean_val = statistics.mean(cpu_scores)
        median_val = statistics.median(cpu_scores)
        mode_val = statistics.mode(cpu_scores) if len(set(cpu_scores)) < len(cpu_scores) else None
        std_dev = statistics.stdev(cpu_scores) if len(cpu_scores) > 1 else 0.0
        min_val = min(cpu_scores)
        max_val = max(cpu_scores)
        
        return {
            'cpu_model': cpu_model,
            'count': len(cpu_scores),
            'mean': round(mean_val, 2),
            'median': round(median_val, 2),
            'mode': round(mode_val, 2) if mode_val else None,
            'std_dev': round(std_dev, 2),
            'min': round(min_val, 2),
            'max': round(max_val, 2),
            'range': round(max_val - min_val, 2),
            'scores': cpu_scores
        }
    
    def get_all_cpu_stats(self) -> Dict[str, Dict]:
        """
        Get statistics for all CPU models found in the dataset.
        
        Returns:
            Dictionary mapping CPU model names to their statistics.
        """
        scores = self._load_scores()
        cpu_models = set(s.get('system', {}).get('processor_model') 
                        for s in scores if 'system' in s and 'processor_model' in s['system'])
        
        return {model: self.get_stats_for_cpu(model) for model in cpu_models}
    
    def get_platform_summary(self, platform: str) -> Dict[str, Any]:
        """
        Get aggregated statistics for a specific platform.
        
        Returns:
            Dictionary with platform-level stats including all CPUs on that platform.
        """
        scores = self._load_scores()
        platform_scores = [s for s in scores 
                          if s.get('system', {}).get('platform') == platform]
        
        if not platform_scores:
            return {'error': f'No data found for platform: {platform}'}
        
        all_ops = [s['ops_per_second'] for s in platform_scores]
        cpu_models_on_platform = set(s.get('system', {}).get('processor_model') 
                                     for s in platform_scores)
        
        return {
            'platform': platform,
            'total_samples': len(platform_scores),
            'cpu_count': len(cpu_models_on_platform),
            'mean_ops': round(statistics.mean(all_ops), 2) if all_ops else 0,
            'median_ops': round(statistics.median(all_ops), 2) if all_ops else 0,
            'std_dev': round(statistics.stdev(all_ops), 2) if len(all_ops) > 1 else 0,
            'min_ops': round(min(all_ops), 2) if all_ops else 0,
            'max_ops': round(max(all_ops), 2) if all_ops else 0,
            'cpu_models': list(cpu_models_on_platform)
        }
    
    # ==================== TREND DETECTION ====================
    
    def detect_trend(self, cpu_model: str, window_size: int = 5) -> Dict[str, Any]:
        """
        Detect performance trends for a CPU model over time.
        Uses linear regression on recent samples to determine direction and magnitude.
        
        Args:
            cpu_model: The CPU model to analyze
            window_size: Number of most recent samples to consider
        
        Returns:
            Dictionary with trend analysis results including direction, slope,
            confidence level, and sample data points.
        """
        scores = self._load_scores()
        cpu_data = [(s['timestamp'], s['ops_per_second']) for s in scores
                   if s.get('system', {}).get('processor_model') == cpu_model]
        
        # Sort by timestamp and take most recent samples
        cpu_data.sort(key=lambda x: datetime.strptime(x[0], "%Y-%m-%d %H:%M:%S"))
        recent_data = cpu_data[-window_size:] if len(cpu_data) >= window_size else cpu_data
        
        if len(recent_data) < 2:
            return {
                'cpu_model': cpu_model,
                'trend_direction': 'insufficient_data',
                'slope': 0.0,
                'confidence': 'low',
                'message': f'Not enough data points ({len(recent_data)}) for trend analysis'
            }
        
        # Convert timestamps to numeric values (seconds from first sample)
        first_ts = datetime.strptime(recent_data[0][0], "%Y-%m-%d %H:%M:%S")
        x_values = [(datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") - first_ts).total_seconds() 
                   for ts, _ in recent_data]
        y_values = [ops for _, ops in recent_data]
        
        # Simple linear regression
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x ** 2 for x in x_values)
        
        denominator = n * sum_x2 - sum_x ** 2
        if denominator == 0:
            return {
                'cpu_model': cpu_model,
                'trend_direction': 'flat',
                'slope': 0.0,
                'confidence': 'medium',
                'message': 'All samples at same timestamp'
            }
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n
        
        # Calculate R-squared for confidence
        y_mean = sum_y / n
        ss_tot = sum((y - y_mean) ** 2 for y in y_values)
        ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(x_values, y_values))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Determine trend direction and confidence
        if abs(slope) < 0.1:
            direction = 'flat'
        elif slope > 0:
            direction = 'improving'
        else:
            direction = 'degrading'
        
        confidence = 'high' if r_squared > 0.8 else ('medium' if r_squared > 0.5 else 'low')
        
        return {
            'cpu_model': cpu_model,
            'trend_direction': direction,
            'slope': round(slope, 4),
            'r_squared': round(r_squared, 3),
            'confidence': confidence,
            'sample_count': len(recent_data),
            'first_sample': recent_data[0][1] if recent_data else None,
            'last_sample': recent_data[-1][1] if recent_data else None,
            'change_percent': round(((recent_data[-1][1] - recent_data[0][1]) / 
                                    recent_data[0][1] * 100) if recent_data and recent_data[0][1] != 0 else 0, 2)
        }
    
    def get_all_trends(self, window_size: int = 5) -> Dict[str, Dict]:
        """
        Get trend analysis for all CPU models.
        
        Returns:
            Dictionary mapping CPU model names to their trend analysis.
        """
        scores = self._load_scores()
        cpu_models = set(s.get('system', {}).get('processor_model') 
                        for s in scores if 'system' in s and 'processor_model' in s['system'])
        return {model: self.detect_trend(model, window_size) for model in cpu_models}
    
    # ==================== COMPARATIVE ANALYSIS ====================
    
    def compare_cpu_profiles(self, cpu1: str, cpu2: str) -> Dict[str, Any]:
        """
        Perform detailed comparative analysis between two CPU models.
        
        Returns:
            Dictionary with head-to-head comparison metrics including
            performance delta, overlap analysis, and statistical significance.
        """
        scores = self._load_scores()
        
        cpu1_data = [s for s in scores if s.get('system', {}).get('processor_model') == cpu1]
        cpu2_data = [s for s in scores if s.get('system', {}).get('processor_model') == cpu2]
        
        if not cpu1_data:
            return {'error': f'No data found for CPU: {cpu1}'}
        if not cpu2_data:
            return {'error': f'No data found for CPU: {cpu2}'}
        
        ops1 = [s['ops_per_second'] for s in cpu1_data]
        ops2 = [s['ops_per_second'] for s in cpu2_data]
        
        mean1, mean2 = statistics.mean(ops1), statistics.mean(ops2)
        std1, std2 = statistics.stdev(ops1) if len(ops1) > 1 else 0,
        statistics.stdev(ops2) if len(ops2) > 1 else 0
        
        # Performance delta (percentage difference)
        delta_percent = ((mean1 - mean2) / mean2 * 100) if mean2 != 0 else 0
        winner = cpu1 if delta_percent > 0 else cpu2
        
        # Overlap analysis
        min1, max1 = min(ops1), max(ops1)
        min2, max2 = min(ops2), max(ops2)
        overlap_start = max(min1, min2)
        overlap_end = min(max1, max2)
        has_overlap = overlap_start <= overlap_end
        
        # Statistical significance (simple t-test approximation)
        pooled_var = ((len(ops1) - 1) * std1**2 + (len(ops2) - 1) * std2**2) / (len(ops1) + len(ops2) - 2)
        se_diff = (pooled_var * (1/len(ops1) + 1/len(ops2))) ** 0.5 if pooled_var > 0 else 0
        t_stat = abs(mean1 - mean2) / se_diff if se_diff > 0 else 0
        
        # Confidence level based on sample sizes and separation
        combined_n = len(ops1) + len(ops2)
        overlap_ratio = (overlap_end - overlap_start) / (max(max1, max2) - min(min1, min1)) if max(max1, max2) > min(min1, min2) else 0
        
        if combined_n >= 10 and overlap_ratio < 0.3:
            significance = 'high'
        elif combined_n >= 5 and overlap_ratio < 0.5:
            significance = 'medium'
        else:
            significance = 'low'
        
        return {
            'cpu1': cpu1,
            'cpu2': cpu2,
            'winner': winner,
            'performance_delta_percent': round(delta_percent, 2),
            'mean_cpu1': round(mean1, 2),
            'mean_cpu2': round(mean2, 2),
            'std_dev_cpu1': round(std1, 2),
            'std_dev_cpu2': round(std2, 2),
            'sample_count_cpu1': len(ops1),
            'sample_count_cpu2': len(ops2),
            'has_performance_overlap': has_overlap,
            'overlap_range': f'{round(overlap_start, 2)}-{round(overlap_end, 2)}' if has_overlap else None,
            'statistical_significance': significance,
            't_statistic': round(t_stat, 3) if se_diff > 0 else 0
        }
    
    def compare_platforms(self, platform1: str, platform2: str) -> Dict[str, Any]:
        """
        Compare overall performance between two platforms.
        
        Returns:
            Dictionary with platform-level comparison metrics.
        """
        scores = self._load_scores()
        
        plat1_data = [s for s in scores if s.get('system', {}).get('platform') == platform1]
        plat2_data = [s for s in scores if s.get('system', {}).get('platform') == platform2]
        
        if not plat1_data:
            return {'error': f'No data found for platform: {platform1}'}
        if not plat2_data:
            return {'error': f'No data found for platform: {platform2}'}
        
        ops1 = [s['ops_per_second'] for s in plat1_data]
        ops2 = [s['ops_per_second'] for s in plat2_data]
        
        mean1, mean2 = statistics.mean(ops1), statistics.mean(ops2)
        std1, std2 = statistics.stdev(ops1) if len(ops1) > 1 else 0,
        statistics.stdev(ops2) if len(ops2) > 1 else 0
        
        delta_percent = ((mean1 - mean2) / mean2 * 100) if mean2 != 0 else 0
        winner = platform1 if delta_percent > 0 else platform2
        
        return {
            'platform1': platform1,
            'platform2': platform2,
            'winner': winner,
            'performance_delta_percent': round(delta_percent, 2),
            'mean_ops_platform1': round(mean1, 2),
            'mean_ops_platform2': round(mean2, 2),
            'std_dev_platform1': round(std1, 2),
            'std_dev_platform2': round(std2, 2),
            'sample_count_platform1': len(ops1),
            'sample_count_platform2': len(ops2),
            'cpu_models_platform1': list(set(s.get('system', {}).get('processor_model') for s in plat1_data)),
            'cpu_models_platform2': list(set(s.get('system', {}).get('processor_model') for s in plat2_data))
        }
    
    # ==================== TIME-BASED ANALYSIS ====================
    
    def get_scores_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Filter scores within a specific date range.
        
        Returns:
            List of score dictionaries within the specified range.
        """
        scores = self._load_scores()
        filtered = []
        for s in scores:
            ts_str = s.get('timestamp')
            if ts_str:
                try:
                    ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                    if start_date <= ts <= end_date:
                        filtered.append(s)
                except ValueError:
                    pass
        return filtered
    
    def get_time_series_data(self, cpu_model: str) -> List[Tuple[datetime, float]]:
        """
        Get time-series data for a CPU model.
        
        Returns:
            List of (timestamp, ops_per_second) tuples sorted chronologically.
        """
        scores = self._load_scores()
        cpu_data = [(datetime.strptime(s['timestamp'], "%Y-%m-%d %H:%M:%S"), s['ops_per_second'])
                   for s in scores if s.get('system', {}).get('processor_model') == cpu_model]
        return sorted(cpu_data, key=lambda x: x[0])
    
    # ==================== UTILITY METHODS ====================
    
    def get_unique_cpu_models(self) -> List[str]:
        """Get list of all unique CPU models in the dataset."""
        scores = self._load_scores()
        return sorted(set(s.get('system', {}).get('processor_model') 
                        for s in scores if 'system' in s and 'processor_model' in s['system']))
    
    def get_unique_platforms(self) -> List[str]:
        """Get list of all unique platforms in the dataset."""
        scores = self._load_scores()
        return sorted(set(s.get('system', {}).get('platform') 
                        for s in scores if 'system' in s and 'platform' in s['system']))
    
    def get_overall_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics across all benchmark data.
        
        Returns:
            Dictionary with global stats including total samples,
            overall mean/std dev, and breakdown by platform/CPU.
        """
        scores = self._load_scores()
        if not scores:
            return {'error': 'No benchmark data available'}
        
        all_ops = [s['ops_per_second'] for s in scores]
        cpu_models = set(s.get('system', {}).get('processor_model') 
                        for s in scores if 'system' in s and 'processor_model' in s['system'])
        platforms = set(s.get('system', {}).get('platform') 
                       for s in scores if 'system' in s and 'platform' in s['system'])
        
        return {
            'total_samples': len(scores),
            'cpu_model_count': len(cpu_models),
            'platform_count': len(platforms),
            'overall_mean_ops': round(statistics.mean(all_ops), 2) if all_ops else 0,
            'overall_median_ops': round(statistics.median(all_ops), 2) if all_ops else 0,
            'overall_std_dev': round(statistics.stdev(all_ops), 2) if len(all_ops) > 1 else 0,
            'overall_min_ops': round(min(all_ops), 2) if all_ops else 0,
            'overall_max_ops': round(max(all_ops), 2) if all_ops else 0,
            'cpu_models': list(cpu_models),
            'platforms': list(platforms)
        }
    
    # ==================== REPORT GENERATION ====================
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive analytics summary report.
        
        Returns:
            Dictionary containing all analytics data in a structured format.
        """
        return {
            'generated_at': datetime.now().isoformat(),
            'overall_statistics': self.get_overall_statistics(),
            'cpu_model_stats': {k: v for k, v in self.get_all_cpu_stats().items() if 'error' not in v},
            'platform_summaries': {
                p: self.get_platform_summary(p)
                for p in self.get_unique_platforms()
                if 'error' not in self.get_platform_summary(p)
            },
            'trends': {k: v for k, v in self.get_all_trends().items() if v.get('trend_direction') != 'insufficient_data'},
            'comparisons': {}
        }
    
    def get_stats_per_cpu_model(self) -> Dict[str, Dict]:
        """
        Get comprehensive statistics per CPU model including performance metrics
        and benchmark duration analysis.
        
        This method provides a detailed breakdown of ops_per_second statistics
        (mean, median, std_dev, min, max) along with duration_seconds statistics
        for each unique CPU model found in the benchmark dataset.
        
        Args:
            None - uses cached or freshly loaded scores from disk.
        
        Returns:
            Dictionary mapping CPU model names to nested dictionaries containing:
                - sample_count: Number of benchmark runs for this CPU
                - ops_per_second: Dict with mean, median, std_dev, min, max values
                - duration_seconds: Dict with mean, median, min, max values
        """
        scores = self._load_scores()
        cpu_models = set(s.get('system', {}).get('processor_model')
                        for s in scores if 'system' in s and 'processor_model' in s['system'])
        
        result = {}
        for model in cpu_models:
            model_scores = [s for s in scores if s.get('system', {}).get('processor_model') == model]
            ops_values = [s['ops_per_second'] for s in model_scores]
            durations = [s['duration_seconds'] for s in model_scores]
            
            result[model] = {
                'sample_count': len(model_scores),
                'ops_per_second': {
                    'mean': round(statistics.mean(ops_values), 2) if ops_values else 0,
                    'median': round(statistics.median(ops_values), 2) if ops_values else 0,
                    'std_dev': round(statistics.stdev(ops_values), 2) if len(ops_values) > 1 else 0,
                    'min': round(min(ops_values), 2) if ops_values else 0,
                    'max': round(max(ops_values), 2) if ops_values else 0
                },
                'duration_seconds': {
                    'mean': round(statistics.mean(durations), 4) if durations else 0,
                    'median': round(statistics.median(durations), 4) if durations else 0,
                    'min': round(min(durations), 4) if durations else 0,
                    'max': round(max(durations), 4) if durations else 0
                }
            }
        return result
    
    def get_scores_by_cpu_model(self) -> Dict[str, List[float]]:
        """
        Retrieve all benchmark scores organized by CPU model.
        
        This method groups raw ops_per_second values by their associated
        processor model, providing a simple lookup structure for further
        analysis or visualization.
        
        Args:
            None - uses cached or freshly loaded scores from disk.
        
        Returns:
            Dictionary mapping each CPU model name to a list of its
            ops_per_second benchmark values. Models with no data are excluded.
        """
        scores = self._load_scores()
        result = defaultdict(list)
        for s in scores:
            model = s.get('system', {}).get('processor_model')
            if model:
                result[model].append(s['ops_per_second'])
        return dict(result)
    
    def detect_trends(self, scores: List[float]) -> Dict[str, Any]:
        """
        Analyze a sequence of benchmark scores to determine performance trends.
        
        This method calculates the percentage change between the first and last
        score values to classify the trend as improving, degrading, or stable.
        It is useful for quick trend assessment without full time-series analysis.
        
        Args:
            scores: List of float values representing benchmark results in order.
        
        Returns:
            Dictionary containing:
                - trend: One of 'improving', 'degrading', or 'stable'
                - change_rate: Percentage change from first to last score
        """
        if len(scores) < 2:
            return {'trend': 'insufficient_data', 'change_rate': 0.0}
        
        first = scores[0]
        last = scores[-1]
        change_rate = ((last - first) / first * 100) if first != 0 else 0
        
        if abs(change_rate) < 2:
            direction = 'stable'
        elif change_rate > 0:
            direction = 'improving'
        else:
            direction = 'degrading'
        
        return {'trend': direction, 'change_rate': round(change_rate, 1)}
    
    def get_trend_visualization(self, scores: List[float]) -> str:
        """
        Generate a text-based sparkline visualization.
        Returns ASCII art representation of the trend.
        """
        if not scores:
            return 'N/A'
        
        min_val = min(scores)
        max_val = max(scores)
        range_val = max_val - min_val if max_val != min_val else 1
        
        # Create a simple bar chart representation
        width = min(len(scores), 30)  # Limit display width
        height = 5
        
        lines = []
        for row in range(height, 0, -1):
            threshold = min_val + (row / height) * range_val
            line_chars = ['█' if s >= threshold else '░' for s in scores[:width]]
            lines.append(''.join(line_chars))
        
        return '\n'.join(lines)
    
    def clear_cache(self) -> None:
        """Clear the internal scores cache."""
        self._scores_cache = None
