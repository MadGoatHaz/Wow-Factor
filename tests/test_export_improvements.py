#!/usr/bin/env python3
"""
Test script for verifying CSV export functionality through core exporters.
Tests the consolidated export mechanism used by ViewBestScoresScreen and ExportMenuScreen.
"""

import os
import sys
import tempfile
import csv
from unittest.mock import patch, MagicMock

# Add the project root to Python path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.screens.views import ViewBestScoresScreen, CompareCPUScreen, ViewAllScoresScreen
from ui.screens.views.rendering import ExportMenuScreen


def test_csv_export_via_core_exporter():
    """Test that CSV export works correctly using core CsvExporter."""

    print("Testing CSV export via core CsvExporter...")

    original_cwd = os.getcwd()
    sample_data = [
        {"processor_model": "Intel Core i7-9700K", "platform": "Linux",
         "ops_per_second": 123456789, "num_threads": 8, "timestamp": "2026-01-01 12:00"},
        {"processor_model": "AMD Ryzen 7 5800X", "platform": "Linux",
         "ops_per_second": 987654321, "num_threads": 16, "timestamp": "2026-01-02 12:00"},
    ]

    try:
        # Test ViewBestScoresScreen data flows through CsvExporter
        print("\n1. Testing ViewBestScoresScreen CSV export via core:")
        screen = ViewBestScoresScreen()
        screen.current_data = sample_data

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            try:
                from core.exporters import CsvExporter
                CsvExporter.export(screen.current_data, "best_scores.csv")
                assert os.path.exists("best_scores.csv"), "CSV file was not created"
                with open("best_scores.csv") as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                    assert len(rows) >= 2, f"Expected at least 2 rows, got {len(rows)}"
                print("   ViewBestScoresScreen CSV export test passed")
            finally:
                os.chdir(original_cwd)

        # Test ExportMenuScreen CSV export
        print("\n2. Testing ExportMenuScreen CSV export:")
        menu = ExportMenuScreen(sample_data)
        assert menu.data == sample_data

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            try:
                from core.exporters import CsvExporter
                CsvExporter.export(menu.data, "best_scores.csv")
                assert os.path.exists("best_scores.csv"), "CSV file was not created"
                print("   ExportMenuScreen CSV export test passed")
            finally:
                os.chdir(original_cwd)

        # Test JSON export
        print("\n3. Testing JSON export:")
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            try:
                from core.exporters import JsonExporter
                JsonExporter.export(sample_data, "best_scores.json")
                assert os.path.exists("best_scores.json"), "JSON file was not created"
                import json
                with open("best_scores.json") as f:
                    data = json.load(f)
                    assert isinstance(data, list) or isinstance(data, dict)
                print("   JSON export test passed")
            finally:
                os.chdir(original_cwd)

        print("\n All export tests passed!")
    except Exception:
        os.chdir(original_cwd)
        raise


def test_screen_has_no_export_to_csv():
    """Verify screens no longer have standalone export_to_csv method (moved to ExportMenuScreen)."""
    from ui.screens.views.rendering import ViewBestScoresScreen

    screen = ViewBestScoresScreen()
    # export_to_csv was removed; export is now handled by ExportMenuScreen
    assert not hasattr(screen, 'export_to_csv'), \
        "ViewBestScoresScreen should not have export_to_csv method anymore"
    print("   Screen correctly lacks standalone export_to_csv method")


if __name__ == "__main__":
    test_csv_export_via_core_exporter()
    test_screen_has_no_export_to_csv()
    print("\nAll tests passed successfully!")