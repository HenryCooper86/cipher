class PasswordGeneratorError(Exception):
    """Base exception for all password generator errors."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class EncryptionError(PasswordGeneratorError):
    """Raised when encryption/decryption operations fail."""
    pass


class ValidationError(PasswordGeneratorError):
    """Raised when input validation fails."""
    pass


class FileOperationError(PasswordGeneratorError):
    """Raised when file operations fail (read, write, delete)."""
    pass


class NetworkError(PasswordGeneratorError):
    """Raised when network operations fail (API calls, breach checks)."""
    pass


class ConfigurationError(PasswordGeneratorError):
    """Raised when configuration is invalid or missing."""
    pass


class ClipboardError(PasswordGeneratorError):
    """Raised when clipboard operations fail."""
    pass


class AuthenticationError(PasswordGeneratorError):
    """Raised when master password authentication fails."""
    pass


class HistoryError(PasswordGeneratorError):
    """Raised when history operations fail."""
    pass
