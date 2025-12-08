#!/usr/bin/env python3
"""
Test script to verify CSV export functionality for all data viewing screens.
"""

import os
import sys
import tempfile
import csv
from datetime import datetime

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.components import ViewBestScoresScreen, CompareCPUScreen, ViewAllScoresScreen
from textual.app import App
from textual.widgets import DataTable

def test_view_best_scores_export():
    """Test export functionality for ViewBestScoresScreen"""
    print("Testing ViewBestScoresScreen export...")
    
    # Create a mock screen instance
    screen = ViewBestScoresScreen()
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            # Mock the table data
            class MockColumn:
                def __init__(self, label):
                    self.label = label
                    
            class MockTable:
                def __init__(self):
                    self.columns = {
                        "rank": MockColumn("Rank"),
                        "cpu_model": MockColumn("CPU Model"),
                        "platform": MockColumn("Platform"),
                        "ops_per_second": MockColumn("Ops/Second"),
                        "timestamp": MockColumn("Timestamp")
                    }
                    self.rows = []
                    
                def get_cell(self, row, key):
                    idx = list(self.columns.keys()).index(key)
                    return row[idx]
            
            table = MockTable()
            table.rows.append(["#1", "Intel i7-9700K", "Linux", "1,234,567", "20250101_120000"])
            table.rows.append(["#2", "AMD Ryzen 7 5800X", "Windows", "987,654", "20250101_130000"])
            
            # Mock the query_one method to return our test table
            def mock_query_one(selector, widget_type=None):
                if selector == "#best_scores_table":
                    return table
                elif selector == "#loading_display":
                    class MockStatic:
                        def update(self, text):
                            print(f"Loading display updated: {text}")
                        def display(self, show):
                            pass
                    return MockStatic()
                return None
            
            screen.query_one = mock_query_one
            
            # Test the export method
            try:
                screen.export_to_csv()
                # Check if CSV file was created
                files = os.listdir(temp_dir)
                csv_files = [f for f in files if f.endswith('.csv')]
                print(f"Created CSV files: {csv_files}")
                
                if csv_files:
                    # Read and verify the content
                    with open(csv_files[0], 'r') as f:
                        reader = csv.reader(f)
                        headers = next(reader)
                        rows = list(reader)
                        
                        print(f"Headers: {headers}")
                        print(f"Rows: {rows}")
                        
                        expected_headers = ["Rank", "CPU Model", "Platform", "Ops/Second", "Timestamp"]
                        if headers == expected_headers:
                            print("✓ Headers match expected")
                        else:
                            print("✗ Headers don't match")
                            
                        if len(rows) >= 1:
                            print("✓ Data rows created")
                        else:
                            print("✗ No data rows found")
                else:
                    print("✗ No CSV file was created")
                    
            except Exception as e:
                print(f"Error during export: {e}")
                
        finally:
            os.chdir(original_cwd)

def test_compare_cpu_export():
    """Test export functionality for CompareCPUScreen"""
    print("\nTesting CompareCPUScreen export...")
    
    # Create a mock screen instance
    screen = CompareCPUScreen()
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            # Mock the table data
            class MockColumn:
                def __init__(self, label):
                    self.label = label
                    
            class MockTable:
                def __init__(self):
                    self.columns = {
                        "rank": MockColumn("Rank"),
                        "platform": MockColumn("Platform"),
                        "ops_per_second": MockColumn("Ops/Second"),
                        "timestamp": MockColumn("Timestamp")
                    }
                    self.rows = []
                    
                def get_cell(self, row, key):
                    idx = list(self.columns.keys()).index(key)
                    return row[idx]
            
            table = MockTable()
            table.rows.append(["#1", "Linux", "1,234,567", "20250101_120000"])
            table.rows.append(["#2", "Windows", "987,654", "20250101_130000"])
            
            # Mock the query_one method to return our test table
            def mock_query_one(selector, widget_type=None):
                if selector == "#cpu_comparison_table":
                    return table
                elif selector == "#loading_display":
                    class MockStatic:
                        def update(self, text):
                            print(f"Loading display updated: {text}")
                        def display(self, show):
                            pass
                    return MockStatic()
                return None
            
            screen.query_one = mock_query_one
            
            # Test the export method
            try:
                screen.export_to_csv()
                # Check if CSV file was created
                files = os.listdir(temp_dir)
                csv_files = [f for f in files if f.endswith('.csv')]
                print(f"Created CSV files: {csv_files}")
                
                if csv_files:
                    # Read and verify the content
                    with open(csv_files[0], 'r') as f:
                        reader = csv.reader(f)
                        headers = next(reader)
                        rows = list(reader)
                        
                        print(f"Headers: {headers}")
                        print(f"Rows: {rows}")
                        
                        expected_headers = ["Rank", "Platform", "Ops/Second", "Timestamp"]
                        if headers == expected_headers:
                            print("✓ Headers match expected")
                        else:
                            print("✗ Headers don't match")
                            
                        if len(rows) >= 1:
                            print("✓ Data rows created")
                        else:
                            print("✗ No data rows found")
                else:
                    print("✗ No CSV file was created")
                    
            except Exception as e:
                print(f"Error during export: {e}")
                
        finally:
            os.chdir(original_cwd)

def test_view_all_scores_export():
    """Test export functionality for ViewAllScoresScreen"""
    print("\nTesting ViewAllScoresScreen export...")
    
    # Create a mock screen instance
    screen = ViewAllScoresScreen()
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            # Mock the table data
            class MockColumn:
                def __init__(self, label):
                    self.label = label
                    
            class MockTable:
                def __init__(self):
                    self.columns = {
                        "rank": MockColumn("Rank"),
                        "cpu_model": MockColumn("CPU Model"),
                        "platform": MockColumn("Platform"),
                        "ops_per_second": MockColumn("Ops/Second"),
                        "timestamp": MockColumn("Timestamp")
                    }
                    self.rows = []
                    
                def get_cell(self, row, key):
                    idx = list(self.columns.keys()).index(key)
                    return row[idx]
            
            table = MockTable()
            table.rows.append(["#1", "Intel i7-9700K", "Linux", "1,234,567", "20250101_120000"])
            table.rows.append(["#2", "AMD Ryzen 7 5800X", "Windows", "987,654", "20250101_130000"])
            
            # Mock the query_one method to return our test table
            def mock_query_one(selector, widget_type=None):
                if selector == "#all_scores_table":
                    return table
                elif selector == "#loading_display":
                    class MockStatic:
                        def update(self, text):
                            print(f"Loading display updated: {text}")
                        def display(self, show):
                            pass
                    return MockStatic()
                return None
            
            screen.query_one = mock_query_one
            
            # Test the export method
            try:
                screen.export_to_csv()
                # Check if CSV file was created
                files = os.listdir(temp_dir)
                csv_files = [f for f in files if f.endswith('.csv')]
                print(f"Created CSV files: {csv_files}")
                
                if csv_files:
                    # Read and verify the content
                    with open(csv_files[0], 'r') as f:
                        reader = csv.reader(f)
                        headers = next(reader)
                        rows = list(reader)
                        
                        print(f"Headers: {headers}")
                        print(f"Rows: {rows}")
                        
                        expected_headers = ["Rank", "CPU Model", "Platform", "Ops/Second", "Timestamp"]
                        if headers == expected_headers:
                            print("✓ Headers match expected")
                        else:
                            print("✗ Headers don't match")
                            
                        if len(rows) >= 1:
                            print("✓ Data rows created")
                        else:
                            print("✗ No data rows found")
                else:
                    print("✗ No CSV file was created")
                    
            except Exception as e:
                print(f"Error during export: {e}")
                
        finally:
            os.chdir(original_cwd)

if __name__ == "__main__":
    print("Running export functionality tests...")
    
    test_view_best_scores_export()
    test_compare_cpu_export()
    test_view_all_scores_export()
    
    print("\nTest completed.")