"""CLI error message formatting."""

from pwd_generator.cli.errors import format_cli_error_text
from pwd_generator.exceptions import (
    EncryptionError,
    FileOperationError,
    HistoryError,
    ValidationError,
)


def test_format_validation_error():
    text = format_cli_error_text(ValidationError("bad length"))
    assert text is not None
    assert "Validation failed" in text
    assert "bad length" in text


def test_format_file_operation_with_details():
    text = format_cli_error_text(
        FileOperationError("write failed", details={"path": "/tmp/x"})
    )
    assert text is not None
    assert "File operation failed" in text
    assert "path" in text


def test_format_encryption_includes_hints():
    text = format_cli_error_text(EncryptionError("decrypt failed"))
    assert text is not None
    assert "Encryption error" in text
    assert "master password" in text.lower()


def test_format_history_error():
    text = format_cli_error_text(HistoryError("index out of range"))
    assert text is not None
    assert "History operation failed" in text


def test_unknown_exception_returns_none():
    assert format_cli_error_text(RuntimeError("boom")) is None
