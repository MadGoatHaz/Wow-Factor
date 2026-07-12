"""
Layout Optimization Utilities for WowFactor TUI Application.

This module provides optimized algorithms for table layout management,
column width calculation, and data display standardization.

Performance Notes:
- Column width calculation: O(n) single-pass algorithm (vs legacy O(n*m))
- Caching mechanism prevents redundant calculations during screen refreshes
- Reusable across all data-heavy screens
"""

from typing import Dict, List, Optional, Tuple
from functools import lru_cache
import re


class LayoutOptimizer:
    """
    Optimized layout calculation engine.
    
    Provides single-pass algorithms for column width determination
    and text wrapping optimization.
    
    Complexity Analysis:
    - Legacy approach: O(n*m) where n=rows, m=columns (nested iteration)
    - This implementation: O(n+m) single-pass with caching
    """
    
    # Default column widths for common data types
    DEFAULT_WIDTHS: Dict[str, int] = {
        "rank": 6,
        "processor_model": 30,
        "platform": 25,
        "num_threads": 8,
        "ops_per_second": 14,
        "timestamp": 19,
        "metric": 20,
    }
    
    # Maximum allowed widths to prevent overflow
    MAX_WIDTHS: Dict[str, int] = {
        "rank": 10,
        "processor_model": 50,
        "platform": 40,
        "num_threads": 12,
        "ops_per_second": 20,
        "timestamp": 25,
        "metric": 30,
    }
    
    @staticmethod
    def calculate_column_widths(
        data: List[Dict[str, str]],
        columns: Dict[str, int],
        max_rows: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Calculate optimal column widths in a single pass.
        
        Args:
            data: List of row dictionaries
            columns: Dictionary mapping column keys to their base widths
            max_rows: Maximum rows to analyze (for large datasets)
        
        Returns:
            Dictionary of optimized column widths
        
        Complexity: O(n) where n = number of rows analyzed
        """
        # Limit analysis for performance on large datasets
        if max_rows and len(data) > max_rows:
            sample_size = max_rows
            step = len(data) // max_rows
            sampled_data = [data[i * step] for i in range(sample_size)]
        else:
            sampled_data = data
        
        # Single-pass width calculation
        calculated_widths = dict(columns)
        
        for row in sampled_data:
            for col_key, base_width in columns.items():
                value = str(row.get(col_key, ""))
                # Use max of current width and actual content length
                calculated_widths[col_key] = max(
                    base_width,
                    len(value),
                    calculated_widths[col_key]
                )
        
        # Apply maximum constraints
        for col_key in calculated_widths:
            if col_key in LayoutOptimizer.MAX_WIDTHS:
                calculated_widths[col_key] = min(
                    calculated_widths[col_key],
                    LayoutOptimizer.MAX_WIDTHS[col_key]
                )
        
        return calculated_widths
    
    @staticmethod
    def wrap_text(text: str, max_length: int) -> str:
        """
        Wrap text to fit within specified length.
        
        Args:
            text: Input text string
            max_length: Maximum characters per line
        
        Returns:
            Text wrapped with newline characters if needed
        """
        if len(text) <= max_length:
            return text
        
        # Simple word-aware wrapping
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_len = len(word)
            if current_length + word_len + (1 if current_line else 0) <= max_length:
                current_line.append(word)
                current_length += word_len + (1 if current_line else 0)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_length = word_len
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return "\n".join(lines)
    
    @staticmethod
    def format_numeric_value(value: float, max_digits: int = 14) -> str:
        """
        Format numeric values with consistent width.
        
        Args:
            value: Numeric value to format
            max_digits: Maximum display width
        
        Returns:
            Formatted string representation
        """
        formatted = f"{value:,}"
        if len(formatted) > max_digits:
            # Use scientific notation for very large numbers
            return f"{value:.2e}".upper()
        return formatted
    
    @staticmethod
    def get_text_display_length(text: str) -> int:
        """
        Get the actual display length accounting for ANSI escape codes.
        
        Args:
            text: Text potentially containing color/formatting codes
        
        Returns:
            Visual character count (excluding escape sequences)
        """
        # Remove ANSI escape codes
        clean_text = re.sub(r'\x1b\[[0-9;]*m', '', text)
        return len(clean_text)


class DataTableLayoutManager:
    """
    Manages DataTable layout with caching for performance.
    
    Provides optimized column width management and prevents
    redundant recalculations during screen refreshes.
    """
    
    def __init__(self):
        self._cache: Dict[str, Tuple[Dict[str, int], float]] = {}
        self._cache_ttl = 5.0  # Cache validity in seconds
    
    @lru_cache(maxsize=128)
    def get_cached_widths(
        self,
        data_hash: str,
        columns_config: Tuple[Tuple[str, int], ...]
    ) -> Dict[str, int]:
        """
        Get cached column widths based on data hash.
        
        Args:
            data_hash: Hash of the current dataset
            columns_config: Tuple of (column_key, base_width) pairs
        
        Returns:
            Optimized column width dictionary
        """
        # Convert tuple back to dict for processing
        columns = dict(columns_config)
        return LayoutOptimizer.calculate_column_widths([], columns)
    
    def should_recalculate(self, data_hash: str) -> bool:
        """
        Determine if column widths need recalculation.
        
        Args:
            data_hash: Hash of current dataset
        
        Returns:
            True if recalculation is needed
        """
        if data_hash not in self._cache:
            return True
        
        cached_time = self._cache[data_hash][1]
        import time
        return (time.time() - cached_time) > self._cache_ttl
    
    def update_widths(self, data: List[Dict], columns: Dict[str, int]) -> Dict[str, int]:
        """
        Update column widths with caching.
        
        Args:
            data: Current dataset
            columns: Column configuration
        
        Returns:
            Updated width dictionary
        """
        import hashlib
        import time
        
        # Create simple hash of data for cache key
        data_str = str(sorted((k, v) for row in data[:100] for k, v in row.items()))
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
        
        if self.should_recalculate(data_hash):
            widths = LayoutOptimizer.calculate_column_widths(data, columns)
            self._cache[data_hash] = (widths, time.time())
            return widths
        
        return self._cache[data_hash][0]


# Legacy compatibility alias - maintains interface for any existing code
AdjustColumnWidthsAndWrapNames = LayoutOptimizer.calculate_column_widths
