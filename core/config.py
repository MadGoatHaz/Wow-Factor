#!/usr/bin/env python3
"""
Configuration management for WowFactor TUI.
Handles loading, saving, and validating application settings.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime

from core.schema import validate_config

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

    def to_dict(self) -> dict[str, int]:
        return {
            "duration": self.duration,
            "num_threads": self.num_threads,
            "batch_runs": self.batch_runs,
            "cooldown_seconds": self.cooldown_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, int | str]) -> BenchmarkDefaults:
        return cls(
            duration=data.get("duration", 15),
            num_threads=data.get("num_threads", 1),
            batch_runs=data.get("batch_runs", 5),
            cooldown_seconds=data.get("cooldown_seconds", 5),
        )


@dataclass
class BenchmarkProfile:
    """Named benchmark profile with custom settings."""
    name: str
    defaults: BenchmarkDefaults
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, int | str]:
        return {
            "name": self.name,
            "defaults": self.defaults.to_dict(),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, int | str]) -> BenchmarkProfile:
        return cls(
            name=data.get("name", "Unnamed"),
            defaults=BenchmarkDefaults.from_dict(data.get("defaults", {})),
            created_at=datetime.fromisoformat(
                data.get("created_at", datetime.now().isoformat())
            ),
        )


class ConfigManager:
    """
    Manages application configuration including defaults and profiles.

    Configuration is stored in JSON files under ~/.config/wowfactor/
    """

    def __init__(self, config_dir: str | None = None) -> None:
        self.config_dir: str = config_dir or CONFIG_DIR
        self.defaults_file: str = os.path.join(self.config_dir, "defaults.json")
        self.profiles_file: str = os.path.join(self.config_dir, "benchmark_profiles.json")

        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)

        # Load defaults
        self._defaults: BenchmarkDefaults = self._load_defaults()

        # Load profiles
        self._profiles: dict[str, BenchmarkProfile] = self._load_profiles()

    def _load_defaults(self) -> BenchmarkDefaults:
        """Load default settings from file or use built-in defaults."""
        try:
            if os.path.exists(self.defaults_file):
                with open(self.defaults_file) as f:
                    data = json.load(f)
                    return BenchmarkDefaults.from_dict(data.get("defaults", {}))
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not load defaults file: {e}")

        # Return fresh defaults if file doesn't exist or is invalid
        return BenchmarkDefaults()

    def _load_profiles(self) -> dict[str, BenchmarkProfile]:
        """Load benchmark profiles from file.

        Validates loaded JSON against the schema. Malformed configs
        produce a warning and empty profile dict; valid data is
        deserialized into BenchmarkProfile instances.
        """
        profiles: dict[str, BenchmarkProfile] = {}
        try:
            if os.path.exists(self.profiles_file):
                with open(self.profiles_file) as f:
                    data = json.load(f)

                # Schema-level validation
                is_valid, errors = validate_config(data)
                if not is_valid:
                    error_msg = "; ".join(errors)
                    print(f"Warning: profiles file failed schema validation: {error_msg}")
                    return profiles

                for name, profile_data in data.get("profiles", {}).items():
                    profiles[name] = BenchmarkProfile.from_dict(profile_data)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not load profiles file: {e}")
        except Exception as e:
            print(f"Warning: Unexpected error loading profiles: {e}")

        return profiles

    def save_defaults(self) -> bool:
        """Save current defaults to configuration file."""
        try:
            data = {"defaults": self._defaults.to_dict()}
            with open(self.defaults_file, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except OSError as e:
            print(f"Error saving defaults: {e}")
            return False

    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate the current in-memory configuration against the schema.

        Checks every profile dict (via BenchmarkProfile.to_dict()) against
        the schema. Returns (valid, errors).

        Returns:
            Tuple of (is_valid, list_of_error_strings).
        """
        data = {
            "profiles": {
                name: profile.to_dict()
                for name, profile in self._profiles.items()
            }
        }
        return validate_config(data)

    def save_profiles(self) -> bool:
        """Save all profiles to configuration file.

        Validates the configuration against the schema before writing.
        Returns False without writing if validation fails.
        """
        # Validate before writing
        is_valid, errors = self.validate_config()
        if not is_valid:
            error_msg = "; ".join(errors)
            print(f"Error: profiles failed schema validation — not saving: {error_msg}")
            return False

        try:
            data = {
                "profiles": {name: profile.to_dict() for name, profile in self._profiles.items()}
            }
            with open(self.profiles_file, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except OSError as e:
            print(f"Error saving profiles: {e}")
            return False

    def get_defaults(self) -> BenchmarkDefaults:
        """Get current default settings."""
        return self._defaults

    def set_defaults(
        self,
        duration: int | None = None,
        num_threads: int | None = None,
        batch_runs: int | None = None,
        cooldown_seconds: int | None = None,
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
        cooldown_seconds: int = 5,
    ) -> bool:
        """Create a new benchmark profile."""
        if name in self._profiles:
            print(f"Profile '{name}' already exists.")
            return False

        defaults = BenchmarkDefaults(
            duration=duration,
            num_threads=num_threads,
            batch_runs=batch_runs,
            cooldown_seconds=cooldown_seconds,
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
        duration: int | None = None,
        num_threads: int | None = None,
        batch_runs: int | None = None,
        cooldown_seconds: int | None = None,
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
