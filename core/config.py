#!/usr/bin/env python3
"""
Configuration management for WowFactor TUI.
Handles loading, saving, and validating application settings.
"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


# Configuration directory
CONFIG_DIR: str = os.path.expanduser("~/.config/wowfactor")
DEFAULTS_FILE: str = os.path.join(CONFIG_DIR, "defaults.json")
PROFILES_FILE: str = os.path.join(CONFIG_DIR, "benchmark_profiles.json")


@dataclass
class BenchmarkDefaults:
    """Default settings for benchmark runs."""
    duration: int = 15
    num_threads: int = 1
    batch_runs: int = 5
    cooldown_seconds: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "duration": self.duration,
            "num_threads": self.num_threads,
            "batch_runs": self.batch_runs,
            "cooldown_seconds": self.cooldown_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BenchmarkDefaults':
        return cls(
            duration=data.get("duration", 15),
            num_threads=data.get("num_threads", 1),
            batch_runs=data.get("batch_runs", 5),
            cooldown_seconds=data.get("cooldown_seconds", 5)
        )


@dataclass
class BenchmarkProfile:
    """Named benchmark profile with custom settings."""
    name: str
    defaults: BenchmarkDefaults
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "defaults": self.defaults.to_dict(),
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BenchmarkProfile':
        return cls(
            name=data.get("name", "Unnamed"),
            defaults=BenchmarkDefaults.from_dict(data.get("defaults", {})),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        )


class ConfigManager:
    """
    Manages application configuration including defaults and profiles.
    
    Configuration is stored in JSON files under ~/.config/wowfactor/
    """
    
    def __init__(self, config_dir: Optional[str] = None) -> None:
        self.config_dir = config_dir or CONFIG_DIR
        self.defaults_file = os.path.join(self.config_dir, "defaults.json")
        self.profiles_file = os.path.join(self.config_dir, "benchmark_profiles.json")
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Load defaults
        self._defaults = self._load_defaults()
        
        # Load profiles
        self._profiles: Dict[str, BenchmarkProfile] = self._load_profiles()
    
    def _load_defaults(self) -> BenchmarkDefaults:
        """Load default settings from file or use built-in defaults."""
        try:
            if os.path.exists(self.defaults_file):
                with open(self.defaults_file, 'r') as f:
                    data = json.load(f)
                    return BenchmarkDefaults.from_dict(data.get("defaults", {}))
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load defaults file: {e}")
        
        # Return fresh defaults if file doesn't exist or is invalid
        return BenchmarkDefaults()
    
    def _load_profiles(self) -> Dict[str, BenchmarkProfile]:
        """Load benchmark profiles from file."""
        profiles = {}
        try:
            if os.path.exists(self.profiles_file):
                with open(self.profiles_file, 'r') as f:
                    data = json.load(f)
                    for name, profile_data in data.get("profiles", {}).items():
                        profiles[name] = BenchmarkProfile.from_dict(profile_data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load profiles file: {e}")
        
        return profiles
    
    def save_defaults(self) -> bool:
        """Save current defaults to configuration file."""
        try:
            data = {"defaults": self._defaults.to_dict()}
            with open(self.defaults_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving defaults: {e}")
            return False
    
    def save_profiles(self) -> bool:
        """Save all profiles to configuration file."""
        try:
            data = {
                "profiles": {name: profile.to_dict() for name, profile in self._profiles.items()}
            }
            with open(self.profiles_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving profiles: {e}")
            return False
    
    def get_defaults(self) -> BenchmarkDefaults:
        """Get current default settings."""
        return self._defaults
    
    def set_defaults(
        self,
        duration: Optional[int] = None,
        num_threads: Optional[int] = None,
        batch_runs: Optional[int] = None,
        cooldown_seconds: Optional[int] = None
    ) -> bool:
        """Update default settings and save to file."""
        if duration is not None:
            self._defaults.duration = duration
        if num_threads is not None:
            self._defaults.num_threads = num_threads
        if batch_runs is not None:
            self._defaults.batch_runs = batch_runs
        if cooldown_seconds is not None:
            self._defaults.cooldown_seconds = cooldown_seconds
        
        return self.save_defaults()
    
    def get_profile(self, name: str) -> Optional[BenchmarkProfile]:
        """Get a specific profile by name."""
        return self._profiles.get(name)
    
    def get_all_profiles(self) -> Dict[str, BenchmarkProfile]:
        """Get all saved profiles."""
        return self._profiles
    
    def create_profile(
        self,
        name: str,
        duration: int = 15,
        num_threads: int = 1,
        batch_runs: int = 5,
        cooldown_seconds: int = 5
    ) -> bool:
        """Create a new benchmark profile."""
        if name in self._profiles:
            print(f"Profile '{name}' already exists.")
            return False
        
        defaults = BenchmarkDefaults(
            duration=duration,
            num_threads=num_threads,
            batch_runs=batch_runs,
            cooldown_seconds=cooldown_seconds
        )
        
        self._profiles[name] = BenchmarkProfile(name=name, defaults=defaults)
        return self.save_profiles()
    
    def delete_profile(self, name: str) -> bool:
        """Delete a benchmark profile."""
        if name not in self._profiles:
            print(f"Profile '{name}' does not exist.")
            return False
        
        del self._profiles[name]
        return self.save_profiles()
    
    def update_profile(
        self,
        name: str,
        duration: Optional[int] = None,
        num_threads: Optional[int] = None,
        batch_runs: Optional[int] = None,
        cooldown_seconds: Optional[int] = None
    ) -> bool:
        """Update an existing profile."""
        if name not in self._profiles:
            print(f"Profile '{name}' does not exist.")
            return False
        
        profile = self._profiles[name]
        
        if duration is not None:
            profile.defaults.duration = duration
        if num_threads is not None:
            profile.defaults.num_threads = num_threads
        if batch_runs is not None:
            profile.defaults.batch_runs = batch_runs
        if cooldown_seconds is not None:
            profile.defaults.cooldown_seconds = cooldown_seconds
        
        return self.save_profiles()


# Global config manager instance
config_manager: ConfigManager = ConfigManager()
