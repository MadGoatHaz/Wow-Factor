#!/usr/bin/env python3
"""
Test script for verifying CSV export improvements in ui_components.py.
This script tests the enhanced CSV export functionality with proper error handling.
"""

import os
import sys
import tempfile
import csv
from unittest.mock import patch, MagicMock

# Add the project root to Python path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.screens.views import ViewBestScoresScreen, CompareCPUScreen, ViewAllScoresScreen


def test_csv_export_functionality():
    """Test that CSV export works correctly in all three screen classes."""
    
    print("Testing CSV export functionality...")
    
    # Test with ViewBestScoresScreen
    print("\n1. Testing ViewBestScoresScreen CSV export:")
    try:
        screen = ViewBestScoresScreen()
        
        # Mock the table data to simulate having data
        mock_table = MagicMock()
        mock_table.columns = [
            MagicMock(label="Rank"),
            MagicMock(label="CPU Model"),
            MagicMock(label="Platform"),
            MagicMock(label="Ops/Second"),
            MagicMock(label="Timestamp")
        ]
        mock_table.column_keys = ["rank", "cpu_model", "platform", "ops_per_second", "timestamp"]
        
        # Mock rows with data
        mock_row1 = MagicMock()
        mock_row1.__iter__ = lambda: iter([1, "Intel Core i7-9700K", "Linux", "123456789", "2023-01-01 12:00"])
        mock_row2 = MagicMock()
        mock_row2.__iter__ = lambda: iter([2, "AMD Ryzen 7 5800X", "Linux", "987654321", "2023-01-02 12:00"])
        
        mock_table.rows = [mock_row1, mock_row2]
        
        # Mock get_cell_value method
        def mock_get_cell_value(row, key):
            if row == mock_row1:
                return {"rank": 1, "cpu_model": "Intel Core i7-9700K", "platform": "Linux",
                        "ops_per_second": "123456789", "timestamp": "2023-01-01 12:00"}[key]
            elif row == mock_row2:
                return {"rank": 2, "cpu_model": "AMD Ryzen 7 5800X", "platform": "Linux",
                        "ops_per_second": "987654321", "timestamp": "2023-01-02 12:00"}[key]
            return ""
        
        mock_table.get_cell_value = mock_get_cell_value
        
        # Mock the query_one method to return our mock table
        with patch.object(screen, 'query_one') as mock_query_one:
            mock_query_one.return_value = mock_table
            
            # Test export_to_csv method (this should not raise an exception)
            screen.export_to_csv()
            
            print("   ✓ ViewBestScoresScreen CSV export test passed")
            
    except Exception as e:
        print(f"   ✗ ViewBestScoresScreen CSV export test failed: {e}")
        assert False, f"ViewBestScoresScreen CSV export test failed: {e}"

    # Test with CompareCPUScreen
    print("\n2. Testing CompareCPUScreen CSV export:")
    try:
        screen = CompareCPUScreen()

        # Mock the table data to simulate having data
        mock_table = MagicMock()
        mock_table.columns = [
            MagicMock(label="Rank"),
            MagicMock(label="Platform"),
            MagicMock(label="Ops/Second"),
            MagicMock(label="Timestamp")
        ]
        mock_table.column_keys = ["rank", "platform", "ops_per_second", "timestamp"]

        # Mock rows with data
        mock_row1 = MagicMock()
        mock_row1.__iter__ = lambda: iter([1, "Linux", "123456789", "2023-01-01 12:00"])
        mock_row2 = MagicMock()
        mock_row2.__iter__ = lambda: iter([2, "Windows", "987654321", "2023-01-02 12:00"])

        mock_table.rows = [mock_row1, mock_row2]

        # Mock get_cell_value method
        def mock_get_cell_value(row, key):
            if row == mock_row1:
                return {"rank": 1, "platform": "Linux", "ops_per_second": "123456789",
                        "timestamp": "2023-01-01 12:00"}[key]
            elif row == mock_row2:
                return {"rank": 2, "platform": "Windows", "ops_per_second": "987654321",
                        "timestamp": "2023-01-02 12:00"}[key]
            return ""

        mock_table.get_cell_value = mock_get_cell_value

        # Mock the query_one method to return our mock table
        with patch.object(screen, 'query_one') as mock_query_one:
            mock_query_one.return_value = mock_table

            # Test export_to_csv method (this should not raise an exception)
            screen.export_to_csv()

            print("   ✓ CompareCPUScreen CSV export test passed")

    except Exception as e:
        print(f"   ✗ CompareCPUScreen CSV export test failed: {e}")
        assert False, f"CompareCPUScreen CSV export test failed: {e}"

    # Test with ViewAllScoresScreen
    print("\n3. Testing ViewAllScoresScreen CSV export:")
    try:
        screen = ViewAllScoresScreen()

        # Mock the table data to simulate having data
        mock_table = MagicMock()
        mock_table.columns = [
            MagicMock(label="Rank"),
            MagicMock(label="CPU Model"),
            MagicMock(label="Platform"),
            MagicMock(label="Ops/Second"),
            MagicMock(label="Timestamp")
        ]
        mock_table.column_keys = ["rank", "cpu_model", "platform", "ops_per_second", "timestamp"]

        # Mock rows with data
        mock_row1 = MagicMock()
        mock_row1.__iter__ = lambda: iter([1, "Intel Core i7-9700K", "Linux", "123456789", "2023-01-01 12:00"])
        mock_row2 = MagicMock()
        mock_row2.__iter__ = lambda: iter([2, "AMD Ryzen 7 5800X", "Linux", "987654321", "2023-01-02 12:00"])

        mock_table.rows = [mock_row1, mock_row2]

        # Mock get_cell_value method
        def mock_get_cell_value(row, key):
            if row == mock_row1:
                return {"rank": 1, "cpu_model": "Intel Core i7-9700K", "platform": "Linux",
                        "ops_per_second": "123456789", "timestamp": "2023-01-01 12:00"}[key]
            elif row == mock_row2:
                return {"rank": 2, "cpu_model": "AMD Ryzen 7 5800X", "platform": "Linux",
                        "ops_per_second": "987654321", "timestamp": "2023-01-02 12:00"}[key]
            return ""

        mock_table.get_cell_value = mock_get_cell_value

        # Mock the query_one method to return our mock table
        with patch.object(screen, 'query_one') as mock_query_one:
            mock_query_one.return_value = mock_table

            # Test export_to_csv method (this should not raise an exception)
            screen.export_to_csv()

            print("   ✓ ViewAllScoresScreen CSV export test passed")

    except Exception as e:
        print(f"   ✗ ViewAllScoresScreen CSV export test failed: {e}")
        assert False, f"ViewAllScoresScreen CSV export test failed: {e}"

    print("\n✓ All CSV export tests passed!")


if __name__ == "__main__":
    success = test_csv_export_functionality()
    sys.exit(0 if success else 1)