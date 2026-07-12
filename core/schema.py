#!/usr/bin/env python3
"""
JSON schema validation for ConfigManager benchmark profiles.

Provides schema definitions and validation functions for the
benchmark profile JSON format used by core.config.ConfigManager.

Schema supports two formats:
  1. New schema: {name, cpu_duration, warmup_duration, algorithms}
  2. Legacy format: {name, defaults, created_at} (for backward compatibility)

The validate_profile() function accepts either format.
"""

from typing import Any, Dict, List, Tuple


# Predefined set of valid algorithm identifiers
VALID_ALGORITHMS: frozenset = frozenset({
    "mips",
    "fft",
    "compress",
    "encrypt",
    "hash",
    "matrix",
    "shuffle",
    "sort",
    "kmeans",
    "convolution",
    "raytrace",
    "predint",
    "lantern",
    "stress-ng",
    "unixbench",
    "sysbench",
    "toplev",
    "perf",
    "cpuinfo",
    "ddr-bandwidth",
    "single-thread",
    "multi-thread",
})


def _check_required_keys(
    data: Dict[str, Any],
    required: List[str],
    path: str = "profile"
) -> List[str]:
    """Check that all required keys are present in data.

    Args:
        data: Dictionary to check.
        required: List of required key names.
        path: Human-readable path prefix for error messages.

    Returns:
        List of error strings (empty if all keys present).
    """
    errors: List[str] = []
    for key in required:
        if key not in data:
            errors.append(f"{path}: missing required key '{key}'")
    return errors


def _validate_string(
    value: Any,
    field_name: str,
    path: str,
    *,
    non_empty: bool = False
) -> List[str]:
    """Validate that a value is a string, optionally non-empty.

    Args:
        value: Value to validate.
        field_name: Name of the field for error messages.
        path: Human-readable path prefix.
        non_empty: If True, reject empty strings.

    Returns:
        List of error strings (empty if valid).
    """
    errors: List[str] = []
    if not isinstance(value, str):
        errors.append(f"{path}.{field_name}: expected string, got {type(value).__name__}")
    elif non_empty and not value.strip():
        errors.append(f"{path}.{field_name}: string must be non-empty")
    return errors


def _validate_positive_number(
    value: Any,
    field_name: str,
    path: str,
    *,
    minimum: float = 0,
    exclusive_minimum: bool = False
) -> List[str]:
    """Validate that a value is a number within bounds.

    Args:
        value: Value to validate.
        field_name: Name of the field for error messages.
        path: Human-readable path prefix.
        minimum: Minimum allowed value.
        exclusive_minimum: If True, value must be strictly greater than minimum.

    Returns:
        List of error strings (empty if valid).
    """
    errors: List[str] = []
    if not isinstance(value, (int, float)):
        # Explicitly reject booleans (bool is subclass of int in Python)
        if isinstance(value, bool):
            errors.append(
                f"{path}.{field_name}: expected number, got boolean"
            )
        else:
            errors.append(
                f"{path}.{field_name}: expected number, got {type(value).__name__}"
            )
    else:
        if exclusive_minimum and value <= minimum:
            errors.append(
                f"{path}.{field_name}: value must be greater than {minimum}"
            )
        elif value < minimum:
            errors.append(
                f"{path}.{field_name}: value must be at least {minimum}"
            )
    return errors


def _validate_string_list(
    value: Any,
    field_name: str,
    path: str,
    *,
    non_empty: bool = False,
    allowed: frozenset = None
) -> List[str]:
    """Validate that a value is a list of strings from an allowed set.

    Args:
        value: Value to validate.
        field_name: Name of the field for error messages.
        path: Human-readable path prefix.
        non_empty: If True, reject empty lists.
        allowed: Set of allowed string values (or None for any string).

    Returns:
        List of error strings (empty if valid).
    """
    errors: List[str] = []
    if not isinstance(value, list):
        errors.append(
            f"{path}.{field_name}: expected list, got {type(value).__name__}"
        )
        return errors

    if non_empty and len(value) == 0:
        errors.append(f"{path}.{field_name}: list must be non-empty")
        return errors

    for i, item in enumerate(value):
        if not isinstance(item, str):
            errors.append(
                f"{path}.{field_name}[{i}]: expected string, got {type(item).__name__}"
            )
            continue

        if allowed and item not in allowed:
            errors.append(
                f"{path}.{field_name}[{i}]: "
                f"'{item}' is not a recognized algorithm. "
                f"Valid options: {sorted(allowed)}"
            )

    return errors


def validate_profile(data: Any) -> Tuple[bool, List[str]]:
    """Validate a benchmark profile dictionary against the schema.

    Accepts two formats:
      New schema:  {name, cpu_duration, warmup_duration, algorithms}
      Legacy:      {name, defaults, [created_at]}

    Args:
        data: The profile data to validate (should be a dict).

    Returns:
        Tuple of (is_valid, errors). errors is an empty list when valid.
    """
    if not isinstance(data, dict):
        return False, [f"profile: expected dict, got {type(data).__name__}"]

    errors: List[str] = []

    # Check name (required in both formats)
    errors.extend(
        _validate_string(data.get("name"), "name", "profile", non_empty=True)
    )

    # Detect format by checking for presence of new schema keys
    has_new_keys = any(k in data for k in ("cpu_duration", "algorithms"))
    has_legacy_keys = "defaults" in data

    if has_new_keys:
        # Validate against new schema
        errors.extend(_validate_profile_new(data, "profile"))
    elif has_legacy_keys:
        # Validate legacy format: name (checked above), defaults (dict),
        # created_at (optional string)
        errors.extend(_validate_profile_legacy(data, "profile"))
    else:
        # No recognized format keys — check for missing new-format keys
        errors.append(
            "profile: unrecognized format. "
            "Expected keys: name (plus either cpu_duration/algorithms or defaults)"
        )

    is_valid = len(errors) == 0
    return is_valid, errors


def _validate_profile_new(data: Dict[str, Any], path: str) -> List[str]:
    """Validate a profile using the new schema format.

    Required keys: name, cpu_duration, warmup_duration, algorithms.
    """
    errors: List[str] = []

    errors.extend(
        _validate_positive_number(
            data.get("cpu_duration"),
            "cpu_duration",
            path,
            minimum=0,
            exclusive_minimum=True,
        )
    )

    errors.extend(
        _validate_positive_number(
            data.get("warmup_duration"),
            "warmup_duration",
            path,
            minimum=0,
            exclusive_minimum=False,
        )
    )

    errors.extend(
        _validate_string_list(
            data.get("algorithms"),
            "algorithms",
            path,
            non_empty=True,
            allowed=VALID_ALGORITHMS,
        )
    )

    return errors


def _validate_profile_legacy(data: Dict[str, Any], path: str) -> List[str]:
    """Validate a profile using the legacy format.

    Required keys: name (already checked), defaults (must be dict with
    recognized numeric fields).
    """
    errors: List[str] = []

    defaults = data.get("defaults")
    if defaults is not None:
        if not isinstance(defaults, dict):
            errors.append(f"{path}.defaults: expected dict, got {type(defaults).__name__}")
        else:
            # Validate that numeric fields are numbers (lenient — allow missing)
            numeric_fields = ("duration", "num_threads", "batch_runs", "cooldown_seconds")
            for field in numeric_fields:
                if field in defaults and not isinstance(defaults[field], (int, float)):
                    if isinstance(defaults[field], bool):
                        errors.append(
                            f"{path}.defaults.{field}: expected number, got boolean"
                        )

    return errors


def validate_config(data: Any) -> Tuple[bool, List[str]]:
    """Validate a complete benchmark configuration file contents.

    Expected structure: {"profiles": {name: profile_dict, ...}}

    Each profile is validated with validate_profile(). The overall
    structure is also checked.

    Args:
        data: The parsed JSON data to validate (should be a dict).

    Returns:
        Tuple of (is_valid, errors). errors is empty when valid.
    """
    if not isinstance(data, dict):
        return False, [
            f"config: expected dict, got {type(data).__name__}"
        ]

    errors: List[str] = []

    # Check top-level structure
    if "profiles" not in data:
        errors.append("config: missing required key 'profiles'")
        return False, errors

    profiles = data.get("profiles")
    if not isinstance(profiles, dict):
        errors.append(
            f"config.profiles: expected dict, got {type(profiles).__name__}"
        )
        return False, errors

    # Empty profile set is valid — user may have deleted all profiles
    # and should be able to save an empty state.

    # Validate each profile
    for name, profile_data in profiles.items():
        is_valid, profile_errors = validate_profile(profile_data)
        if not is_valid:
            errors.extend(
                [f"config.profiles['{name}']: {err}" for err in profile_errors]
            )

    return len(errors) == 0, errors