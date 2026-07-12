#!/usr/bin/env python3
"""
Tests for configuration management module.
"""

import unittest
import os
import tempfile
import shutil
from datetime import datetime


class TestConfigManager(unittest.TestCase):
    """Test suite for ConfigManager class."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create a temporary directory for test config files
        self.test_config_dir = tempfile.mkdtemp(prefix="wowfactor_test_")
        
        from core.config import ConfigManager, BenchmarkDefaults
        
        self.ConfigManager = ConfigManager
        self.BenchmarkDefaults = BenchmarkDefaults
        self.manager = ConfigManager(config_dir=self.test_config_dir)
    
    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_config_dir, ignore_errors=True)
    
    def test_initial_defaults(self) -> None:
        """Test that initial defaults are set correctly."""
        defaults = self.manager.get_defaults()
        
        self.assertEqual(defaults.duration, 15)
        self.assertEqual(defaults.num_threads, 1)
        self.assertEqual(defaults.batch_runs, 5)
        self.assertEqual(defaults.cooldown_seconds, 5)
    
    def test_set_and_get_defaults(self) -> None:
        """Test setting and getting default values."""
        result = self.manager.set_defaults(
            duration=30,
            num_threads=4,
            batch_runs=10
        )
        
        self.assertTrue(result)
        
        defaults = self.manager.get_defaults()
        self.assertEqual(defaults.duration, 30)
        self.assertEqual(defaults.num_threads, 4)
        self.assertEqual(defaults.batch_runs, 10)
    
    def test_save_and_load_defaults(self) -> None:
        """Test that defaults are persisted to file."""
        self.manager.set_defaults(duration=60)
        
        # Create new manager instance to force reload
        new_manager = self.ConfigManager(config_dir=self.test_config_dir)
        
        self.assertEqual(new_manager.get_defaults().duration, 60)
    
    def test_create_profile(self) -> None:
        """Test creating a new benchmark profile."""
        result = self.manager.create_profile(
            name="gaming",
            duration=20,
            num_threads=8,
            batch_runs=3
        )
        
        self.assertTrue(result)
        self.assertIn("gaming", self.manager.get_all_profiles())
        
        profile = self.manager.get_profile("gaming")
        self.assertEqual(profile.defaults.duration, 20)
        self.assertEqual(profile.defaults.num_threads, 8)
    
    def test_create_duplicate_profile(self) -> None:
        """Test that creating a duplicate profile fails."""
        self.manager.create_profile(name="test", duration=15)
        
        result = self.manager.create_profile(name="test", duration=30)
        
        self.assertFalse(result)
    
    def test_delete_profile(self) -> None:
        """Test deleting a profile."""
        self.manager.create_profile(name="to_delete", duration=15)
        
        result = self.manager.delete_profile("to_delete")
        
        self.assertTrue(result)
        self.assertNotIn("to_delete", self.manager.get_all_profiles())
    
    def test_update_profile(self) -> None:
        """Test updating an existing profile."""
        self.manager.create_profile(name="updated", duration=15, num_threads=2)
        
        result = self.manager.update_profile(
            name="updated",
            duration=45,
            num_threads=16
        )
        
        self.assertTrue(result)
        
        profile = self.manager.get_profile("updated")
        self.assertEqual(profile.defaults.duration, 45)
        self.assertEqual(profile.defaults.num_threads, 16)
    
    def test_get_all_profiles(self) -> None:
        """Test getting all profiles."""
        self.manager.create_profile(name="profile1", duration=10)
        self.manager.create_profile(name="profile2", duration=20)
        self.manager.create_profile(name="profile3", duration=30)
        
        profiles = self.manager.get_all_profiles()
        
        self.assertEqual(len(profiles), 3)
        self.assertIn("profile1", profiles)
        self.assertIn("profile2", profiles)
        self.assertIn("profile3", profiles)
    
    def test_benchmark_defaults_to_dict(self) -> None:
        """Test BenchmarkDefaults to_dict method."""
        defaults = self.BenchmarkDefaults(
            duration=25,
            num_threads=4,
            batch_runs=10,
            cooldown_seconds=10
        )
        
        result = defaults.to_dict()
        
        self.assertEqual(result["duration"], 25)
        self.assertEqual(result["num_threads"], 4)
        self.assertEqual(result["batch_runs"], 10)
        self.assertEqual(result["cooldown_seconds"], 10)
    
    def test_benchmark_defaults_from_dict(self) -> None:
        """Test BenchmarkDefaults from_dict method."""
        data = {
            "duration": 35,
            "num_threads": 6,
            "batch_runs": 8,
            "cooldown_seconds": 15
        }
        
        defaults = self.BenchmarkDefaults.from_dict(data)
        
        self.assertEqual(defaults.duration, 35)
        self.assertEqual(defaults.num_threads, 6)
    
    def test_benchmark_defaults_partial_from_dict(self) -> None:
        """Test from_dict with partial data uses defaults."""
        data = {"duration": 20}  # Only provide duration
        
        defaults = self.BenchmarkDefaults.from_dict(data)
        
        self.assertEqual(defaults.duration, 20)
        self.assertEqual(defaults.num_threads, 1)  # Default value
        self.assertEqual(defaults.batch_runs, 5)    # Default value


if __name__ == "__main__":
    unittest.main()
