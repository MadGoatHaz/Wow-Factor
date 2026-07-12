#!/usr/bin/env python3
"""
Configuration management for WowFactor TUI.
Handles loading, saving, and validating application settings.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

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

    def to_dict(self) -> dict[str, Any]:
        return {
            "duration": self.duration,
            "num_threads": self.num_threads,
            "batch_runs": self.batch_runs,
            "cooldown_seconds": self.cooldown_seconds
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'BenchmarkDefaults':
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "defaults": self.defaults.to_dict(),
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'BenchmarkProfile':
        return cls(
            name=data.get("name", "Unnamed"),
            defaults=BenchmarkDefaults.from_dict(data.get("defaults", {})),
            created_at=datetime.fromisoformat(
                data.get("created_at", datetime.now().isoformat())
            )
        )


class ConfigManager:
    """
    Manages application configuration including defaults and profiles.

    Configuration is stored in JSON files under ~/.config/wowfactor/
    """

    def __init__(self, config_dir: str | None = None) -> None:
        self.config_dir = config_dir or CONFIG_DIR
        self.defaults_file = os.path.join(self.config_dir, "defaults.json")
        self.profiles_file = os.path.join(self.config_dir, "benchmark_profiles.json")

        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)

        # Load defaults
        self._defaults = self._load_defaults()

        # Load profiles
        self._profiles: dict[str, BenchmarkProfile] = self._load_profiles()

    def _load_defaults(self) -> BenchmarkDefaults:
        """Load default settings from file or use built-in defaults."""
        try:
            if os.path.exists(self.defaults_file):
                with open(self.defaults_file) as f:
                    data = json.load(f)
                    logger.info("Loaded defaults from %s", self.defaults_file)
                    return BenchmarkDefaults.from_dict(data.get("defaults", {}))
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Could not load defaults file %s: %s",
                           self.defaults_file, e)

        # Return fresh defaults if file doesn't exist or is invalid
        return BenchmarkDefaults()

    def _load_profiles(self) -> dict[str, BenchmarkProfile]:
        """Load benchmark profiles from file."""
        profiles = {}
        try:
            if os.path.exists(self.profiles_file):
                with open(self.profiles_file) as f:
                    data = json.load(f)
                    for name, profile_data in data.get("profiles", {}).items():
                        profiles[name] = BenchmarkProfile.from_dict(profile_data)
                logger.info("Loaded %d profiles from %s",
                            len(profiles), self.profiles_file)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Could not load profiles file %s: %s",
                           self.profiles_file, e)
        return profiles

    def save_defaults(self) -> bool:
        """Save current defaults to configuration file."""
        try:
            data = {"defaults": self._defaults.to_dict()}
            with open(self.defaults_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info("Saved defaults to %s", self.defaults_file)
            return True
        except OSError as e:
            logger.error("Error saving defaults to %s: %s",
                         self.defaults_file, e)
            return False

    def save_profiles(self) -> bool:
        """Save all profiles to configuration file."""
        try:
            data = {
                "profiles": {name: profile.to_dict()
                             for name, profile in self._profiles.items()}
            }
            with open(self.profiles_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info("Saved %d profiles to %s",
                        len(self._profiles), self.profiles_file)
            return True
        except OSError as e:
            logger.error("Error saving profiles to %s: %s",
                         self.profiles_file, e)
            return False

    def get_defaults(self) -> BenchmarkDefaults:
        """Get current default settings."""
        return self._defaults

    def set_defaults(
        self,
        duration: int | None = None,
        num_threads: int | None = None,
        batch_runs: int | None = None,
        cooldown_seconds: int | None = None
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

    def get_profile(self, name: str) -> BenchmarkProfile | None:
        """Get a specific profile by name."""
        return self._profiles.get(name)

    def get_all_profiles(self) -> dict[str, BenchmarkProfile]:
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
            logger.warning("Profile '%s' already exists", name)
            return False

        defaults = BenchmarkDefaults(
            duration=duration,
            num_threads=num_threads,
            batch_runs=batch_runs,
            cooldown_seconds=cooldown_seconds
        )

        self._profiles[name] = BenchmarkProfile(name=name, defaults=defaults)
        logger.info("Created profile '%s'", name)
        return self.save_profiles()

    def delete_profile(self, name: str) -> bool:
        """Delete a benchmark profile."""
        if name not in self._profiles:
            logger.warning("Profile '%s' does not exist", name)
            return False

        del self._profiles[name]
        logger.info("Deleted profile '%s'", name)
        return self.save_profiles()

    def update_profile(
        self,
        name: str,
        duration: int | None = None,
        num_threads: int | None = None,
        batch_runs: int | None = None,
        cooldown_seconds: int | None = None
    ) -> bool:
        """Update an existing profile."""
        if name not in self._profiles:
            logger.warning("Profile '%s' does not exist", name)
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


config_manager: ConfigManager = ConfigManager()