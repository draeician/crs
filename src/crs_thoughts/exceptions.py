"""Custom exceptions for the crs_thoughts package."""

class CrsThoughtsError(Exception):
    """Base exception for all crs_thoughts errors."""
    pass

class ValidationError(CrsThoughtsError):
    """Raised when input validation fails."""
    pass

class StorageError(CrsThoughtsError):
    """Raised when storage operations fail."""
    pass

class ConfigurationError(CrsThoughtsError):
    """Raised when configuration is invalid or missing."""
    pass 