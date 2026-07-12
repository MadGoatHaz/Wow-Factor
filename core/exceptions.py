"""WowFactor custom exception hierarchy."""

class WowFactorError(Exception):
    """Base exception for all WowFactor errors."""
    pass

class BenchmarkError(WowFactorError):
    """Base exception for benchmark-related errors."""
    pass

class BenchmarkCancelledError(BenchmarkError):
    """Raised when a benchmark is cancelled by the user."""
    pass

class BenchmarkTimeoutError(BenchmarkError):
    """Raised when a benchmark exceeds its timeout."""
    pass

class DataLoadError(BenchmarkError):
    """Raised when benchmark data cannot be loaded."""
    pass

class AnalyticsError(WowFactorError):
    """Base exception for analytics-related errors."""
    pass

class DataInsufficientError(AnalyticsError):
    """Raised when insufficient data for analytics."""
    pass

class ExportError(WowFactorError):
    """Base exception for export-related errors."""
    pass

class FormatUnsupportedError(ExportError):
    """Raised when an export format is not supported."""
    pass

class ConfigError(WowFactorError):
    """Base exception for configuration-related errors."""
    pass

class ConfigValidationError(ConfigError):
    """Raised when configuration validation fails."""
    pass

class SystemErrorCustom(WowFactorError):
    """Base exception for system-level errors."""
    pass
